package main

// 项目 5 的验收标尺：修复前后各跑一次 `go test -bench . -benchmem`，
// allocs/op 的降幅就是判决书。测试只依赖 genCode 与 seedIndex 两个入口，
// 对缺陷版与修复版都成立。

import (
	"fmt"
	"net/http"
	"net/http/httptest"
	"testing"
)

func BenchmarkGenCode(b *testing.B) {
	b.ReportAllocs()
	for i := 0; i < b.N; i++ {
		genCode(fmt.Sprintf("https://example.com/target/%d", i))
	}
}

func BenchmarkRedirect(b *testing.B) {
	pairs := make([][2]string, 0, 5000)
	for i := 1; i <= 5000; i++ {
		pairs = append(pairs, [2]string{fmt.Sprintf("s%05d", i), "https://example.com/x"})
	}
	seedIndex(pairs)

	req := httptest.NewRequest("GET", "/s02500", nil)
	w := httptest.NewRecorder()
	b.ReportAllocs()
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		w.Body.Reset()
		redirectHandler(w, req)
	}
}

var _ = http.StatusOK
