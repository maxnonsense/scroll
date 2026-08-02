from test_utils import wayland_client, wait_for_client_map, ScrollInstance


def _find_view_by_title(node: dict, title: str) -> dict | None:
    if node.get("name") == title and node.get("pid") is not None:
        return node
    for key in ("nodes", "floating_nodes"):
        for child in node.get(key, []):
            found = _find_view_by_title(child, title)
            if found:
                return found
    return None


def _find_workspace(node: dict) -> dict | None:
    if node.get("type") == "workspace":
        return node
    for child in node.get("nodes", []):
        found = _find_workspace(child)
        if found:
            return found
    return None


def _full_height(node: dict) -> int:
    # rect excludes the titlebar, deco_rect is the titlebar
    return node["rect"]["height"] + node.get("deco_rect", {"height": 0}).get(
        "height", 0
    )


def test_columns_split_equally(scroll_compositor: ScrollInstance) -> None:
    """niri-style columns: windows added to a column split the vertical
    space equally, and expand again when windows are removed."""
    inst = scroll_compositor
    with wayland_client(inst, "w1"):
        wait_for_client_map(inst, "w1")
        inst.wait_for_idle()

        tree = inst.get_tree()
        ws = _find_workspace(tree)
        assert ws is not None
        ws_height = ws["rect"]["height"]

        # A single window takes the full workspace height
        n1 = _find_view_by_title(tree, "w1")
        assert n1 is not None
        assert abs(_full_height(n1) - ws_height) <= 5, (
            f"single window height {_full_height(n1)} != workspace {ws_height}"
        )

        # New windows open inside the same column in vertical mode
        res = inst.cmd("set_mode v")
        assert res and res[0]["success"]

        with wayland_client(inst, "w2"):
            wait_for_client_map(inst, "w2")
            inst.wait_for_idle()

            tree = inst.get_tree()
            n1 = _find_view_by_title(tree, "w1")
            n2 = _find_view_by_title(tree, "w2")
            assert n1 is not None and n2 is not None
            h1, h2 = _full_height(n1), _full_height(n2)
            assert abs(h1 - h2) <= 2, f"heights not equal: {h1} vs {h2}"
            assert abs(h1 - ws_height / 2) <= 5, (
                f"height {h1} not half of workspace {ws_height}"
            )

            with wayland_client(inst, "w3"):
                wait_for_client_map(inst, "w3")
                inst.wait_for_idle()

                tree = inst.get_tree()
                heights = []
                for title in ("w1", "w2", "w3"):
                    node = _find_view_by_title(tree, title)
                    assert node is not None
                    heights.append(_full_height(node))
                assert max(heights) - min(heights) <= 2, (
                    f"heights not equal: {heights}"
                )
                assert abs(heights[0] - ws_height / 3) <= 5, (
                    f"height {heights[0]} not a third of workspace {ws_height}"
                )

            # w3 closed: the two remaining windows re-split in half
            inst.wait_for_idle()
            tree = inst.get_tree()
            n1 = _find_view_by_title(tree, "w1")
            n2 = _find_view_by_title(tree, "w2")
            assert n1 is not None and n2 is not None
            h1, h2 = _full_height(n1), _full_height(n2)
            assert abs(h1 - h2) <= 2, f"heights not equal: {h1} vs {h2}"
            assert abs(h1 - ws_height / 2) <= 5, (
                f"height {h1} not half of workspace {ws_height}"
            )

        # w2 closed: w1 expands to the full height again
        inst.wait_for_idle()
        tree = inst.get_tree()
        n1 = _find_view_by_title(tree, "w1")
        assert n1 is not None
        assert abs(_full_height(n1) - ws_height) <= 5


def test_scale_workspaces_toggle(scroll_compositor: ScrollInstance) -> None:
    """The workspaces overview toggles on and off with an animation and
    survives workspace switches while enabled."""
    inst = scroll_compositor
    with wayland_client(inst, "w1"):
        wait_for_client_map(inst, "w1")
        inst.wait_for_idle()

        res = inst.cmd("scale_workspaces toggle")
        assert res and res[0]["success"], f"Command failed: {res}"
        inst.wait_for_idle()
        assert inst.proc.poll() is None, "Compositor crashed enabling overview"

        # Switch workspaces while the overview is active (re-centers it)
        res = inst.cmd("workspace 2")
        assert res and res[0]["success"]
        inst.wait_for_idle()
        res = inst.cmd("workspace 1")
        assert res and res[0]["success"]
        inst.wait_for_idle()
        assert inst.proc.poll() is None, "Compositor crashed switching workspace"

        res = inst.cmd("scale_workspaces toggle")
        assert res and res[0]["success"], f"Command failed: {res}"
        inst.wait_for_idle()
        assert inst.proc.poll() is None, "Compositor crashed disabling overview"

        # Toggle rapidly to exercise animation interruption paths
        for _ in range(4):
            res = inst.cmd("scale_workspaces toggle")
            assert res and res[0]["success"]
        inst.wait_for_idle()
        assert inst.proc.poll() is None, "Compositor crashed in rapid toggling"
