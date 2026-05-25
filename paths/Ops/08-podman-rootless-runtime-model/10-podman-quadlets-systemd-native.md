# Podman — `10-podman-quadlets-systemd-native`

**Focus:** Replace `podman generate systemd` with Quadlet `.container` unit files — the modern, declarative approach for production-grade rootless containers managed by systemd.

**Practise focus**

- Write a `.container` Quadlet file in `~/.config/containers/systemd/` and confirm `systemd --user` picks it up
- Map Quadlet fields to their Compose equivalents: `Image`, `Volume`, `Environment`, `Network`, `PublishPort`
- Enable auto-restart and verify container survives reboot without manual intervention
- Use `.network` Quadlet files to wire multi-container stacks without Compose
- Understand why Quadlets supersede `podman generate systemd` — declarative vs generated, drift-safe, reviewable in git
- Debug Quadlet load failures with `systemctl --user status` and `journalctl --user -u`
- Compare: Quadlet vs Compose vs Kubernetes Pod YAML — when each surface fits
