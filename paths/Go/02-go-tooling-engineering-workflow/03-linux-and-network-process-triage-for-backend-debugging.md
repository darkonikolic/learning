# Unit 3 — Linux and Network Process Triage for Backend Debugging

## Concept

Backend debugging is not just reading code — it is observing a running system. When a service is wedged, slow, or refusing connections, you need to answer: is the process running, what port is it on, how many connections does it have, and is it blocking on I/O or burning CPU? These tools give you ground truth about a running system in seconds, before you touch the codebase.

## Code

```bash
# --- Find the process ---
pgrep -la go-lab               # list PIDs and command lines matching "go-lab"
ps aux | grep go-lab           # broader view with CPU and memory

# --- Check what port it is listening on ---
ss -tlnp | grep 8080           # show TCP listening sockets, grep for port 8080
lsof -i :8080                  # show all processes using port 8080

# --- Inspect open connections for a specific PID ---
lsof -p <pid> | grep TCP       # list open TCP connections for the process
ss -tnp | grep <pid>           # alternative: netstat-like view filtered by pid

# --- Check connection state counts (useful when things look wedged) ---
ss -s                          # summary: LISTEN, ESTAB, CLOSE_WAIT counts
ss -tn state close-wait        # list all CLOSE_WAIT connections (server not reading responses)

# --- Read /proc for low-level info when debuggers unavailable ---
cat /proc/<pid>/limits         # file descriptor limits (ulimit)
ls -la /proc/<pid>/fd | wc -l  # count open file descriptors
cat /proc/<pid>/status         # memory usage, thread count, state

# --- Send signals ---
kill -SIGTERM <pid>            # graceful shutdown — app should handle this
kill -SIGINT <pid>             # same as Ctrl+C
kill -SIGKILL <pid>            # force kill — no cleanup, last resort

# --- Trace syscalls briefly (use on a replica, not production) ---
strace -p <pid> -e trace=network  # show only network syscalls
strace -p <pid> -c                # summary: count syscalls, find the expensive ones
```

```go
// In your Go server: handle SIGTERM for graceful shutdown
package main

import (
	"context"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"
)

func main() {
	srv := &http.Server{Addr: ":8080"}

	go func() {
		if err := srv.ListenAndServe(); err != http.ErrServerClosed {
			log.Fatal(err)
		}
	}()
	log.Println("listening on :8080")

	// Wait for SIGTERM or SIGINT
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGTERM, syscall.SIGINT)
	<-quit

	log.Println("shutting down...")
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err := srv.Shutdown(ctx); err != nil {
		log.Fatal("shutdown error:", err)
	}
	log.Println("server stopped")
}
```

## Exercise

**Build:** Start your `go-lab` server (the HTTP version from module 05, or a minimal `net/http` server on `:8080`).

**Input:** With the server running in one terminal, open another and run the triage commands above.

**Output:** Find the PID, confirm it is listening on 8080 with `ss -tlnp`, check its open file descriptors with `lsof -p <pid>`, then send `SIGTERM` and verify the server logs "server stopped" and exits cleanly.

**Acceptance:** You can answer these without looking at code: what is the PID, what port, how many open FDs. Graceful shutdown completes within 5 seconds.

## Interview

- A service is not accepting new connections but the process is running. What commands help you diagnose this?
- What does a high count of `CLOSE_WAIT` connections indicate?
- When would you reach for `strace` versus `go tool pprof` to diagnose a slow Go service?
