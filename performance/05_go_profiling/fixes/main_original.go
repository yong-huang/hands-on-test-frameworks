// shorturl：本性能系列的被测系统之二（Go）。
//
// 路由只有三件事：短码跳转、创建短链、健康检查。代码里埋了 3 处
// 刻意性能缺陷，答案在 ../SECRET_DEFS.md（做完对应实验前不要看）。
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"sync"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

type link struct {
	code string
	url  string
}

var (
	pool *pgxpool.Pool
	// 【缺陷位之一】用 slice 存全量短链，重定向时线性扫——先别换成 map
	links []link
	// 【缺陷位之一】一把全局锁包住所有读写——先别拆它
	mu sync.Mutex
)

const seedCount = 5000 // DB 里有 5000 条短链，线性扫描的代价随它放大

// HTTP 黄金信号指标：项目 3 的监控栈要抓这两条
var (
	httpDuration = promauto.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "http_request_duration_seconds",
			Help:    "Per-handler latency",
			Buckets: []float64{.005, .01, .025, .05, .1, .25, .5, 1, 2.5, 5, 10},
		},
		[]string{"handler", "method", "code"},
	)
	httpRequests = promauto.NewCounterVec(
		prometheus.CounterOpts{Name: "http_requests_total", Help: "Per-handler requests"},
		[]string{"handler", "method", "code"},
	)
)

// withObs 给每个路由挂上延迟直方图 + 请求计数，handler 标签显式指定
func withObs(name string, h http.HandlerFunc) http.Handler {
	return promhttp.InstrumentHandlerDuration(
		httpDuration.MustCurryWith(prometheus.Labels{"handler": name}),
		promhttp.InstrumentHandlerCounter(
			httpRequests.MustCurryWith(prometheus.Labels{"handler": name}), h))
}

func loadLinks(ctx context.Context) error {
	rows, err := pool.Query(ctx, "SELECT code, url FROM links")
	if err != nil {
		return err
	}
	defer rows.Close()
	for rows.Next() {
		var l link
		if err := rows.Scan(&l.code, &l.url); err != nil {
			return err
		}
		links = append(links, l)
	}
	// 别吞执行期错误（权限/网络类错误会以 rows.Err() 形式出现）
	if err := rows.Err(); err != nil {
		return err
	}
	log.Printf("loaded %d links into memory", len(links))
	return nil
}

func genCode(url string) string {
	// 【缺陷位之一】热循环里用 fmt.Sprintf 逐段拼接——剖析实验里它会自己站出来
	const charset = "abcdefghijklmnopqrstuvwxyz0123456789"
	code := ""
	sum := fnv32a(url)
	for i := 0; i < 1024; i++ {
		code += fmt.Sprintf("%c", charset[(sum+uint32(i))%uint32(len(charset))])
	}
	return code[:8]
}

func fnv32a(s string) uint32 {
	var h uint32 = 2166136261
	for i := 0; i < len(s); i++ {
		h ^= uint32(s[i])
		h *= 16777619
	}
	return h
}

func redirectHandler(w http.ResponseWriter, r *http.Request) {
	code := r.URL.Path[len("/"):]
	mu.Lock()
	defer mu.Unlock() // 【缺陷位之一】锁覆盖了整个线性扫描，读读也互斥
	for _, l := range links {
		if l.code == code {
			http.Redirect(w, r, l.url, http.StatusMovedPermanently)
			return
		}
	}
	http.NotFound(w, r)
}

type shortenIn struct {
	URL string `json:"url"`
}

func shortenHandler(w http.ResponseWriter, r *http.Request) {
	var in shortenIn
	if err := json.NewDecoder(r.Body).Decode(&in); err != nil || in.URL == "" {
		http.Error(w, "invalid body", http.StatusBadRequest)
		return
	}
	code := genCode(in.URL)
	ctx, cancel := context.WithTimeout(r.Context(), 3*time.Second)
	defer cancel()
	if _, err := pool.Exec(ctx,
		"INSERT INTO links (code, url) VALUES ($1, $2) ON CONFLICT (code) DO NOTHING",
		code, in.URL); err != nil {
		http.Error(w, "db error", http.StatusInternalServerError)
		return
	}
	mu.Lock()
	links = append(links, link{code, in.URL})
	mu.Unlock()
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(map[string]string{"code": code})
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	ctx, cancel := context.WithTimeout(r.Context(), 2*time.Second)
	defer cancel()
	if err := pool.Ping(ctx); err != nil {
		http.Error(w, "db unreachable", http.StatusServiceUnavailable)
		return
	}
	w.Write([]byte(`{"status":"ok"}`))
}

func main() {
	dsn := os.Getenv("DATABASE_URL")
	if dsn == "" {
		dsn = "postgres://shorturl:shorturl@postgres:5432/shorturl"
	}
	var err error
	pool, err = pgxpool.New(context.Background(), dsn)
	if err != nil {
		log.Fatal(err)
	}
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	if err := pool.Ping(ctx); err != nil {
		log.Fatal("postgres not reachable: ", err)
	}
	if err := loadLinks(ctx); err != nil {
		log.Fatal(err)
	}

	mux := http.NewServeMux()
	mux.Handle("/healthz", withObs("healthz", healthHandler))
	mux.Handle("/metrics", promhttp.Handler())
	mux.Handle("/api/shorten", withObs("shorten", shortenHandler))
	mux.Handle("/", withObs("redirect", redirectHandler)) // /{code} 兜底路由

	log.Println("shorturl listening on :8932")
	log.Fatal(http.ListenAndServe(":8932", mux))
}
