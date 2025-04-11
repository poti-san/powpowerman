# プラットフォームのロール（デスクトップ、ノートパソコン、……）を取得する。

from powpowerman import PowerPlatform

print(repr(PowerPlatform.get_platform_role_ex()))
