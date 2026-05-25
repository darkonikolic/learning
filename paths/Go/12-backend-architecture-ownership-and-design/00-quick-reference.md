# Quick Reference — Backend Architecture

## Package naming rules
- Name by WHAT it owns, not by what it does (not "utils", "helpers")
- One concept per package
- Avoid import cycles — use interfaces to break them

## Layer dependency direction
cmd → service → domain (types only)
         ↓
    repository (implements service interfaces)

## Interface placement
// Define interfaces WHERE THEY ARE CONSUMED (service layer)
// Implement them WHERE DATA LIVES (repository layer)
// This makes service layer independently testable

## DI: manual wiring in main()
repo := postgres.NewRepo(db)
svc  := service.New(repo)
h    := handler.New(svc)
// If this doesn't compile, your graph is broken

## Domain model rules
- No framework imports in domain/
- Pure Go types + methods
- Business logic lives here, not in handlers
