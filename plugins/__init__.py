"""add-work 的 funcpatch 补丁集。

本模块不导入任何补丁：Python 导入 ``plugins.<子包>`` 前会先执行本文件，
若在此处导入全部补丁，单独引入一个补丁就会连带加载其余补丁。
补丁清单见 :mod:`plugins.specs`，引导入口见 :mod:`plugins.bootstrap`。
"""

from __future__ import annotations
