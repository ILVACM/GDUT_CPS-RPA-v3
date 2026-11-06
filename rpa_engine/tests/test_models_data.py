"""数据层单测（2026-09-21 定稿 M2-T10：uid/分配器/状态机/级联/单一入口）。

纯标准库 unittest，禁 Qt。执行：
    cd rpa_engine && python -m unittest discover -s tests -v
"""

import json
import unittest

from gui.models import WorkflowModel


def make_model(n_tables=2):
    m = WorkflowModel()
    m.set_tables([
        {"table_id": f"T{i}", "alias": f"表{i}", "sqlite_table": f"t{i}",
         "file_path": f"d:/x/f{i}.xlsx", "sheet_name": "S1", "header_row": 1}
        for i in range(1, n_tables + 1)
    ])
    return m


class UidTest(unittest.TestCase):
    def test_uid_generated_and_unique(self):
        m = make_model()
        uids = [t.uid for t in m.tables]
        self.assertTrue(all(uids))
        self.assertEqual(len(set(uids)), len(uids))

    def test_to_dict_excludes_uid(self):
        m = make_model()
        s = m.add_step("filter")
        s.params = {"conditions": []}
        text = json.dumps(m.to_dict(), ensure_ascii=False)
        self.assertNotIn("uid", text)

    def test_load_generates_uid(self):
        m = make_model()
        s = m.add_step("filter")
        data = m.to_dict()
        m2 = WorkflowModel()
        m2.load_from_dict(data)
        self.assertTrue(all(t.uid for t in m2.tables))
        self.assertTrue(all(st.uid for st in m2.steps))


class AllocatorTest(unittest.TestCase):
    def test_first_derived_is_t101(self):
        m = make_model()
        s = m.add_step("filter")
        self.assertEqual(s.output_table_id, "T101")

    def test_deleted_number_reused(self):
        m = make_model()
        s1 = m.add_step("filter")
        self.assertEqual(s1.output_table_id, "T101")
        m.remove_step(0)
        s2 = m.add_step("filter")
        self.assertEqual(s2.output_table_id, "T101")

    def test_no_collision_sequence(self):
        m = make_model()
        ids = []
        for _ in range(5):
            ids.append(m.add_step("filter").output_table_id)
        self.assertEqual(len(set(ids)), 5)
        self.assertEqual(m.validate_table_ids_unique(), [])

    def test_alloc_skips_dangling(self):
        # P6：悬空引用号不被新步夺回（防"复活"口径分裂）
        m = make_model(1)
        s1 = m.add_step("filter")
        out1 = s1.output_table_id
        s2 = m.add_step("aggregate")
        s2.target_table_id = out1
        m.remove_step(0)
        self.assertEqual(m.table_states.get(out1), "dangling")
        s3 = m.add_step("dedup")
        self.assertNotEqual(s3.output_table_id, out1)
        # T101 被 dangling 占用、T102 已被 s2(aggregate) 产出占用 → T103
        self.assertEqual(s3.output_table_id, "T103")

    def test_dangling_released_after_repoint(self):
        # P6：下游重指后悬空号释放复用
        m = make_model(1)
        s1 = m.add_step("filter")
        out1 = s1.output_table_id
        s2 = m.add_step("aggregate")
        s2.target_table_id = out1
        m.remove_step(0)
        s2 = m.steps[0]
        s2.target_table_id = "T1"     # 重指输入表
        m.reconcile()
        self.assertNotIn(out1, m.table_states)
        s3 = m.add_step("filter")
        self.assertEqual(s3.output_table_id, out1)


class TitleTest(unittest.TestCase):
    """步骤实时标题（2026-09-21 审计 P8）。"""

    def test_title_ordinal_shrink(self):
        from gui.models import title_of
        m = make_model(1)
        m.add_step("filter")
        m.add_step("filter")
        m.add_step("filter")
        m.remove_step(1)
        titles = [title_of(m.steps, s.step_id) for s in m.steps]
        self.assertEqual(titles, ["条件筛选 1", "条件筛选 2"])

    def test_title_mixed_types_independent(self):
        from gui.models import title_of
        m = make_model(1)
        s1 = m.add_step("filter")
        s2 = m.add_step("aggregate")
        self.assertEqual(title_of(m.steps, s1.step_id), "条件筛选 1")
        self.assertEqual(title_of(m.steps, s2.step_id), "条件统计 1")

    def test_title_of_fallback(self):
        from gui.models import title_of
        m = make_model(1)
        self.assertEqual(title_of(m.steps, "S999"), "S999")


class StateMachineTest(unittest.TestCase):
    def test_seven_states(self):
        m = make_model(2)
        s1 = m.add_step("filter")          # T1 -> T101
        s1.target_table_id = "T1"
        s2 = m.add_step("aggregate")       # T101 -> T102 (referenced 源)
        s2.target_table_id = s1.output_table_id
        s3 = m.add_step("convert_dtype")   # 不产表
        s3.target_table_id = s2.output_table_id
        m.reconcile()
        st = m.table_states
        self.assertEqual(st["T2"], "declared")
        self.assertEqual(st[s2.output_table_id], "referenced")
        self.assertEqual(st[s1.output_table_id], "referenced")
        # overwritten
        m.set_output_mode(s1.step_id, "overwrite_target")
        self.assertEqual(m.table_states[s1.output_table_id], "overwritten")
        m.set_output_mode(s1.step_id, "new_table")
        # deprecated
        m.deprecate_table("T2", True)
        self.assertEqual(m.table_states["T2"], "deprecated")
        m.deprecate_table("T2", False)
        # dangling
        s3.target_table_id = "T999"
        m.reconcile()
        self.assertEqual(m.table_states["T999"], "dangling")

    def test_produced_state(self):
        # R2：produced 态直接断言（产而不被引→produced；被引→referenced；
        # overwrite→overwritten 优先）
        m = make_model(1)
        s1 = m.add_step("dedup")           # T1 -> T101（无下游引用）
        self.assertEqual(m.table_states[s1.output_table_id], "produced")
        s2 = m.add_step("aggregate")       # T101 -> T102
        s2.target_table_id = s1.output_table_id
        m.reconcile()
        self.assertEqual(m.table_states[s1.output_table_id], "referenced")
        self.assertEqual(m.table_states[s2.output_table_id], "produced")
        s1.params["output_mode"] = "overwrite_target"
        m.reconcile()
        self.assertEqual(m.table_states[s1.output_table_id], "overwritten")

    def test_deprecated_gone_table_purged(self):
        m = make_model()
        s1 = m.add_step("filter")
        out = s1.output_table_id
        m.deprecate_table(out, True)
        self.assertIn(out, m.deprecated_tables)
        m.remove_step(0)
        self.assertNotIn(out, m.deprecated_tables)


class CascadeTest(unittest.TestCase):
    def test_cascade_b_dangling(self):
        m = make_model()
        s1 = m.add_step("filter")
        out1 = s1.output_table_id
        s2 = m.add_step("filter")
        s2.target_table_id = out1
        out2 = s2.output_table_id
        s3 = m.add_step("aggregate")
        s3.target_table_id = out2
        m.deprecate_table(out2, True)
        m.remove_step(0)   # 删 S1 → S2 保留引用 out1（已不存在）→ dangling
        self.assertEqual(m.steps[0].target_table_id, out1)
        self.assertEqual(m.table_states[out1], "dangling")
        # 弃用标记随表消失摘除（out2 仍存在→保留）
        self.assertIn(out2, m.deprecated_tables)
        # step_id 即时连续
        self.assertEqual([s.step_id for s in m.steps], ["S1", "S2"])

    def test_cascade_keeps_extra_refs_dangling(self):
        m = make_model(2)
        s1 = m.add_step("filter")
        out1 = s1.output_table_id
        s2 = m.add_step("mapping_match")
        s2.params["match_table_id"] = out1
        m.remove_step(0)
        self.assertEqual(m.steps[0].params.get("match_table_id"), out1)
        self.assertEqual(m.table_states[out1], "dangling")


class SessionTest(unittest.TestCase):
    def test_reset_steps_keeps_tables(self):
        m = make_model()
        m.add_step("filter")
        m.deprecate_table("T1", True)
        m.reset_steps()
        self.assertEqual(m.steps, [])
        self.assertEqual(len(m.tables), 2)
        self.assertEqual(m.deprecated_tables, set())

    def test_load_session_registry_authoritative(self):
        m = make_model(2)
        s = m.add_step("filter")
        data = m.to_dict()
        # 外部 data.tables 伪造第三张表 → 被 registry 覆盖
        data["tables"].append({"table_id": "T9", "alias": "伪",
                               "sqlite_table": "t9", "source": {}})
        m2 = WorkflowModel()
        m2.load_session([
            {"table_id": "T1", "alias": "表1", "sqlite_table": "t1"},
            {"table_id": "T2", "alias": "表2", "sqlite_table": "t2"},
        ], data)
        self.assertEqual([t.table_id for t in m2.tables], ["T1", "T2"])
        self.assertEqual(len(m2.steps), 1)

    def test_load_to_dict_idempotent(self):
        # M5-a/K1：会话还原走编辑态文件（uid 随文件持久，生产 last_config
        # 即此口径），业务口径再导出幂等；业务 JSON 无 uid 时 load 重生成→
        # 物理名漂移为 K3 预期（见 PhysicalNameUidTest.test_uid_persist_roundtrip）
        m = make_model()
        m.add_step("filter")
        d1 = m.to_dict()
        m2 = WorkflowModel()
        m2.load_session([
            {"table_id": "T1", "alias": "表1", "sqlite_table": "t1"},
            {"table_id": "T2", "alias": "表2", "sqlite_table": "t2"},
        ], m.to_dict(include_deprecated=True))
        d2 = m2.to_dict()
        self.assertEqual(d1["steps"], d2["steps"])
        self.assertEqual(len(d1["tables"]), len(d2["tables"]))

    def test_load_to_dict_idempotent_overwrite(self):
        # 编辑态口径含 output_mode 的往返幂等（2026-09-21 审计 P1）
        m = make_model()
        s = m.add_step("filter")
        s.params = {"conditions": [], "output_mode": "overwrite_target"}
        reg = [{"table_id": "T1", "alias": "表1", "sqlite_table": "t1"},
               {"table_id": "T2", "alias": "表2", "sqlite_table": "t2"}]
        d1 = m.to_dict(include_deprecated=True)
        m2 = WorkflowModel()
        m2.load_session(reg, d1)
        d2 = m2.to_dict(include_deprecated=True)
        self.assertEqual(d1["steps"], d2["steps"])

    def test_apply_registry_keeps_steps(self):
        # P2：确认导入仅刷新表，不清步骤
        m = make_model()
        s1 = m.add_step("filter")
        s2 = m.add_step("aggregate")
        s2.target_table_id = "T9"          # 悬空引用
        m.apply_registry([
            {"table_id": "T1", "alias": "表1", "sqlite_table": "t1"},
            {"table_id": "T2", "alias": "表2", "sqlite_table": "t2"},
        ])
        self.assertEqual(len(m.steps), 2)
        self.assertEqual([t.table_id for t in m.tables], ["T1", "T2"])
        self.assertEqual(m.table_states.get("T9"), "dangling")
        self.assertEqual(m.validate_table_ids_unique(), [])

    def test_load_session_still_clears(self):
        # 两入口语义差异固化：load_session 整会话载入清步骤
        m = make_model()
        m.add_step("filter")
        m.load_session([
            {"table_id": "T1", "alias": "表1", "sqlite_table": "t1"},
            {"table_id": "T2", "alias": "表2", "sqlite_table": "t2"},
        ], {"steps": []})
        self.assertEqual(m.steps, [])


class CollapseTest(unittest.TestCase):
    """_cp 合成步折叠迁移（2026-09-21 审计 P1-b）。"""

    _TABLES = [{"table_id": "T1", "alias": "表1", "sqlite_table": "t1",
                "source": {"file": "d:/x/f1.xlsx", "sheet": "S1",
                           "header_row": 1}}]

    def _cp_dict(self, parent_id="S1", phys="t1", ptype="filter"):
        return {
            "name": "w", "schema_version": "3.1",
            "tables": self._TABLES,
            "steps": [
                {"step_id": parent_id, "type": ptype, "name": "筛选 1",
                 "target_table_id": "T1", "output_table_id": "T101",
                 "params": {"conditions": []}, "on_error": "stop",
                 "retry_count": 3},
                {"step_id": f"{parent_id}_cp", "type": "copy_table",
                 "name": "筛选 1（写回原表）", "target_table_id": "T101",
                 "output_table_id": "",
                 "params": {"output_table": phys}, "on_error": "stop",
                 "retry_count": 3},
            ],
        }

    def test_legacy_cp_collapse(self):
        m = WorkflowModel()
        m.load_from_dict(self._cp_dict())
        self.assertEqual(len(m.steps), 1)
        self.assertEqual(m.steps[0].params.get("output_mode"),
                         "overwrite_target")
        # overwritten 态键=产出表（reconcile 按 produced_by 判定），目标表
        # T1 为 referenced
        self.assertEqual(m.table_states.get("T101"), "overwritten")
        self.assertEqual(m.table_states.get("T1"), "referenced")
        self.assertFalse(any("_cp" in s.step_id for s in m.steps))

    def test_legacy_cp_missing_output_table_param(self):
        d = self._cp_dict()
        d["steps"][1]["params"] = {}
        m = WorkflowModel()
        m.load_from_dict(d)
        self.assertEqual(len(m.steps), 1)
        self.assertEqual(m.steps[0].params.get("output_mode"),
                         "overwrite_target")

    def test_legacy_cp_orphan_kept(self):
        d = self._cp_dict()
        d["steps"][1]["step_id"] = "S9_cp"        # 无前邻/同名父步
        d["steps"][1]["target_table_id"] = "T999"  # 三级兜底（产出==target）落空
        m = WorkflowModel()
        m.load_from_dict(d)   # warning 经 loguru 输出（不入 root logging，
        # 不做 assertLogs 捕获）；行为断言=孤立 _cp 保留不静默丢
        self.assertEqual(len(m.steps), 2)
        self.assertTrue(any(s.step_id == "S9_cp" for s in m.steps))
        # 父步 params 未被误注入 mode
        self.assertNotIn("output_mode", m.steps[0].params)

    def test_cp_non_filter_parent_kept(self):
        # 父步 aggregate（外部手工构造）：折叠执行、结构幂等再展开
        d = self._cp_dict(ptype="aggregate")
        m = WorkflowModel()
        m.load_from_dict(d)
        self.assertEqual(len(m.steps), 1)
        self.assertEqual(m.steps[0].params.get("output_mode"),
                         "overwrite_target")
        biz = m.to_dict()
        self.assertEqual(len(biz["steps"]), 2)   # L644 判 mode 非 op 类型

    def test_double_cp_each_collapsed(self):
        d = self._cp_dict()
        d["steps"].append(dict(d["steps"][1]))
        d["steps"][2]["step_id"] = "S1_cp"      # 连续两个同源 _cp
        m = WorkflowModel()
        m.load_from_dict(d)
        self.assertEqual(len(m.steps), 1)


class CollisionTest(unittest.TestCase):
    def test_validate_detects_dup(self):
        m = make_model()
        s1 = m.add_step("filter")
        s2 = m.add_step("filter")
        s2.output_table_id = s1.output_table_id   # 人为撞号
        self.assertEqual(m.validate_table_ids_unique(),
                         [s1.output_table_id])

    def test_facade_removed_production_entry(self):
        # R6/F5（P3-11）：冗余第三门面已删除；撞号检测走生产入口
        import gui.graph_edges as ge
        self.assertFalse(hasattr(ge, "detect_table_id_collisions"))
        m = make_model()
        s1 = m.add_step("filter")
        s2 = m.add_step("filter")
        s2.output_table_id = s1.output_table_id
        self.assertEqual(m.validate_table_ids_unique(),
                         [s1.output_table_id])


class PhysicalNameUidTest(unittest.TestCase):
    """M5-a：物理名 t_{uid} 与 uid 持久化（§3.3 例1/例2）。"""

    def test_physical_name_is_t_uid(self):
        m = make_model(2)
        s = m.add_step("filter")                     # output_table_id == "T101"
        uid = s.uid
        d = m.to_dict()
        self.assertEqual(d["steps"][0]["params"]["output_table"], f"t_{uid}")
        self.assertNotIn("uid", d["steps"][0])       # 业务口径无 uid 键

    def test_edit_state_uid_key(self):
        m = make_model(2)
        s = m.add_step("filter")
        d2 = m.to_dict(True)
        self.assertEqual(d2["steps"][0]["uid"], s.uid)
        self.assertNotIn("output_table", d2["steps"][0]["params"])
        self.assertEqual(len(d2["steps"][0]), 9)     # 第 9 键
        self.assertEqual(list(d2["steps"][0])[-1], "uid")   # uid 居末位

    def test_duplicate_uid_regenerated(self):
        m = make_model(2)
        a = m.add_step("filter")                     # T101
        b = m.add_step("dedup")                      # T102
        u0 = a.uid
        b.uid = u0                                   # 构造重复
        d = m.to_dict()
        names = [x["params"]["output_table"] for x in d["steps"]]
        self.assertEqual(len(set(names)), 2)         # 导出名唯一
        self.assertEqual(m.steps[0].uid, u0)         # 首现者保留
        self.assertNotEqual(m.steps[1].uid, u0)      # 重复者就地重生成

    def test_uid_persist_roundtrip(self):
        m = make_model(2)
        s = m.add_step("filter")
        m2 = make_model(2)
        m2.load_from_dict(m.to_dict(True))
        self.assertEqual(m2.steps[0].uid, s.uid)     # 编辑态继承
        m3 = make_model(2)
        m3.load_from_dict(m.to_dict())
        self.assertTrue(m3.steps[0].uid)             # 业务口径重生成，非空


class InsertStepTest(unittest.TestCase):
    """M5-b：insert_step 中段插入/clamp/add_step 委托（§4.3 例1-3）。"""

    def _fixture(self):
        m = make_model(2)
        m.add_step("filter")      # T101
        m.add_step("aggregate")   # T102
        m.add_step("export")      # is_end
        return m

    def test_insert_step_middle(self):
        m = self._fixture()
        u = [s.uid for s in m.steps]
        m.insert_step(1, "dedup")
        self.assertEqual(len(m.steps), 4)
        self.assertEqual(m.steps[1].type, "dedup")
        self.assertEqual([s.step_id for s in m.steps],
                         ["S1", "S2", "S3", "S4"])   # 立即重排
        self.assertEqual(
            [m.steps[0].uid, m.steps[2].uid, m.steps[3].uid], u)
        self.assertEqual(m.steps[1].output_table_id, "T103")   # 最小空号

    def test_insert_clamp(self):
        m = self._fixture()
        m.insert_step(99, "dedup")
        self.assertEqual(m.steps[-1].type, "dedup")
        self.assertEqual(m.steps[-1].step_id, "S4")  # 落末尾
        m2 = self._fixture()
        m2.insert_step(-5, "dedup")
        self.assertEqual(m2.steps[0].type, "dedup")
        self.assertEqual(m2.steps[0].step_id, "S1")  # 落首位，均不抛

    def test_add_step_delegates_append(self):
        m = self._fixture()
        m.add_step("filter")
        self.assertEqual(m.steps[-1].type, "filter")
        self.assertEqual(m.steps[-1].step_id, "S4")  # 委托=末尾插入


class OverwriteDerivedTargetTest(unittest.TestCase):
    """R6/A1（P0-1/D1①）：覆盖写回目标为派生表时 cp 步物理名解析。"""

    def _model(self):
        m = make_model(2)
        s1 = m.add_step("filter")          # → T101
        s2 = m.add_step("dedup")           # → T102
        s2.target_table_id = s1.output_table_id   # 写回目标＝派生表 T101
        s2.params = {"key_columns": ["a"], "keep": "first",
                     "output_mode": "overwrite_target"}
        return m, s1, s2

    def test_cp_target_uses_derived_physical_name(self):
        m, s1, s2 = self._model()
        d = m.to_dict()
        self.assertEqual(len(d["steps"]), 3)        # s1、s2、s2_cp
        cp = d["steps"][2]
        self.assertEqual(cp["step_id"], f"{s2.step_id}_cp")
        self.assertEqual(cp["type"], "copy_table")
        # 核心断言：cp 写回物理名＝T101 的 t_{uid}（非逻辑号回退）
        self.assertEqual(cp["params"]["output_table"], f"t_{s1.uid}")
        self.assertNotEqual(cp["params"]["output_table"],
                            s1.output_table_id)

    def test_parent_names_and_edit_mode_regression(self):
        m, s1, s2 = self._model()
        d = m.to_dict()
        self.assertEqual(d["steps"][0]["params"]["output_table"],
                         f"t_{s1.uid}")
        self.assertEqual(d["steps"][1]["params"]["output_table"],
                         f"t_{s2.uid}")
        d_edit = m.to_dict(True)
        self.assertEqual(len(d_edit["steps"]), 2)   # 编辑态不展开 _cp


if __name__ == "__main__":
    unittest.main()
