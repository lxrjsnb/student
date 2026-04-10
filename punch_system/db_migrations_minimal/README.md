# Minimal DB Migrations

这个目录只包含当前项目运行所必需的最小数据库结构，不包含历史遗留的 `score` 字段迁移，也不包含旧阶段的兼容性脚本。

当前项目最小必需表：

1. `users`
2. `user_sessions`
3. `punch_records`
4. `admin_applications`

推荐执行顺序：

1. `00_users.sql`
2. `01_user_sessions.sql`
3. `02_punch_records.sql`
4. `03_admin_applications.sql`

说明：

- `users` 是基础表，其他业务都依赖它。
- `admin_applications` 带外键，必须放在 `users` 之后。
- 当前代码已不依赖 `score` 字段，不要再执行旧的 `add_score_field.sql` / `migrate_score.py`。
- 当前代码会在注册时自动把“系统内第一个注册用户”提升为 `super_admin`，因此这里不额外提供管理员种子数据。
