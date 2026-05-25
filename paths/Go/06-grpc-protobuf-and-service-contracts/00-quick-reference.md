---
# Quick Reference — gRPC & Protobuf

## proto3 basics
```proto
syntax = "proto3";
package user.v1;
option go_package = "github.com/org/repo/gen/user/v1;userv1";

message User {
  int64  id    = 1;
  string email = 2;
}
service UserService {
  rpc GetUser(GetUserRequest) returns (User);
  rpc ListUsers(ListUsersRequest) returns (stream User);
}
```

## Generate
```sh
protoc --go_out=. --go-grpc_out=. user.proto
```

## Server setup
```go
s := grpc.NewServer(
    grpc.UnaryInterceptor(loggingInterceptor),
)
userpb.RegisterUserServiceServer(s, &userServer{})
s.Serve(lis)
```

## Unary interceptor shape
```go
func loggingInterceptor(ctx context.Context, req any,
    info *grpc.UnaryServerInfo, handler grpc.UnaryHandler) (any, error) {
    start := time.Now()
    resp, err := handler(ctx, req)
    log.Printf("%s took %s", info.FullMethod, time.Since(start))
    return resp, err
}
```

## Context deadline (client side)
```go
ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
defer cancel()
resp, err := client.GetUser(ctx, &userpb.GetUserRequest{Id: 1})
```

## Schema evolution rules
```
// SAFE: add new field (gets zero value on old clients)
// SAFE: rename field (wire uses field numbers, not names)
// UNSAFE: change field type or field number
```
