# 画面の明るさを50%に設定する。

from powguid import Guid

from powpowerman import PowerScheme

GUID_DISPLAY_BRIGHTNESS_LEVEL = Guid.from_str("{aded5e82-b909-4619-9949-f5d71dac0bcb}")

display_subgroup = PowerScheme.active_scheme().subgroup_display
display_brightness = display_subgroup.settings(GUID_DISPLAY_BRIGHTNESS_LEVEL)
display_brightness.ac_value_index = 50
# display_brightness.ac_value_index = 100

display_brightness.apply_changes()

pass
