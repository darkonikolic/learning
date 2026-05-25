# Quick Reference — Testing

## Run commands
go test ./...                    # all tests
go test -v -run TestFoo ./...    # specific, verbose
go test -race ./...              # race detection
go test -bench=. -benchmem       # benchmarks
go test -fuzz=FuzzFoo -fuzztime=30s

## Table-driven template
cases := []struct{ name string; input X; want Y }{ ... }
for _, tc := range cases {
    t.Run(tc.name, func(t *testing.T) { ... })
}

## t.Parallel() — safe when
- test uses local vars only (no shared state)
- tc := tc // capture loop var (pre-Go 1.22)

## gomock
ctrl := gomock.NewController(t)
mock.EXPECT().Method(gomock.Any()).Return(val, nil).Times(1)

## testcontainers
wait.ForListeningPort("5432/tcp")
t.Cleanup(func() { container.Terminate(ctx) })
