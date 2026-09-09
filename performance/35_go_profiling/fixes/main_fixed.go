// shorturl 修复版（lab 35 产物）：三处缺陷全部治理。
//
// - D4 线性扫描 → map O(1) 查找
// - D5 热循环 Sprintf → byte slice 直接拼接（1025 allocs → 2 allocs）
// - D6 全局互斥锁 → RWMutex：读路径 RLock，读读不再互斥
package main

import (
	"context"
	"encoding/json"
	"log"
	"net/http"
	_ "net/http/pprof" // 注册 /debug/pprof/* 到 DefaultServeMux（项目 5 的观测面）
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
	// 【D4 修复】map 替代 slice：跳转从 O(n) 线性扫变 O(1)
	links map[string]string
	// 【D6 修复】RWMutex 替代 Mutex：读路径只加读锁
	mu sync.RWMutex
)

const seedCount = 5000

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
	links = make(map[string]string, seedCount+16)
	for rows.Next() {
		var code, url string
		if err := rows.Scan(&code, &url); err != nil {
			return err
		}
		links[code] = url
	}
	if err := rows.Err(); err != nil {
		return err
	}
	log.Printf("loaded %d links into memory", len(links))
	return nil
}

func genCode(url string) string {
	// 【D5 修复】byte slice 一次分配到底：1025 allocs/op → 2 allocs/op
	const charset = "abcdefghijklmnopqrstuvwxyz0123456789"
	buf := make([]byte, 0, 8)
	sum := fnv32a(url)
	for i := 0; i < 8; i++ {
		buf = append(buf, charset[(sum+uint32(i))%uint32(len(charset))])
	}
	return string(buf)
}

func fnv32a(s string) uint32 {
	var h uint32 = 2166136261
	for i := 0; i < len(s); i++ {
		h ^= uint32(s[i])
		h *= 16777619
	}
	return h
}

// seedIndex 给基准测试/剖析灌内存索引（与缺陷版同签名，测试两版通用）
func seedIndex(pairs [][2]string) {
	mu.Lock()
	defer mu.Unlock()
	if links == nil {
		links = make(map[string]string, len(pairs)+16)
	}
	for _, p := range pairs {
		links[p[0]] = p[1]
	}
}

func redirectHandler(w http.ResponseWriter, r *http.Request) {
	code := r.URL.Path[len("/"):]
	mu.RLock() // 【D6 修复】读锁：并发读之间不再互斥
	url, ok := links[code]
	mu.RUnlock()
	if ok {
		http.Redirect(w, r, url, http.StatusMovedPermanently)
		return
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
	if links == nil {
		links = make(map[string]string, 16)
	}
	links[code] = in.URL
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
	mux.Handle("/debug/pprof/", http.DefaultServeMux)
	mux.Handle("/api/shorten", withObs("shorten", shortenHandler))
	mux.Handle("/", withObs("redirect", redirectHandler)) // /{code} 兜底路由

	log.Println("shorturl listening on :8932")
	log.Fatal(http.ListenAndServe(":8932", mux))
}
