"""
Configure a 2x2 slice layout to display a 2-frame sequence as:
- Slice 1: Axial, frame 1
- Slice 2: Sagittal, frame 1
- Slice 3: Axial, frame 2
- Slice 4: Sagittal, frame 2

Usage:
- Copy-paste the entire content into Slicer's Python Interactor and press Enter.
- Or run in the Interactor: exec(open(r'<path-to-this-file>').read())

Notes:
- Requires a SequenceBrowser with a master sequence that has at least 2 items.
- If the 2x2 custom slice layout (tags One/Two/Three/Four) is not present, it will be created automatically.
"""


def configure_sequence_2x2_views(frame1_index: int = 0, frame2_index: int = 1):
    import slicer

    lm = slicer.app.layoutManager()

    # Ensure the 2x2 slice layout with tags One/Two/Three/Four exists and is active
    def ensure_2x2_layout():
        layoutNode = lm.layoutLogic().GetLayoutNode()
        # If any of the expected slice widgets are missing, register/apply our custom layout
        needLayout = False
        for tag in ("One", "Two", "Three", "Four"):
            if lm.sliceWidget(tag) is None:
                needLayout = True
                break
        if needLayout:
            customLayoutId = 556  # arbitrary unique id (must be unique in scene)
            customLayout = r'''
            <layout type="horizontal" split="true">
              <item>
                <layout type="vertical" split="true">
                  <item>
                    <view class="vtkMRMLSliceNode" singletontag="One">
                      <property name="orientation" action="default">Axial</property>
                      <property name="viewlabel" action="default">1</property>
                    </view>
                  </item>
                  <item>
                    <view class="vtkMRMLSliceNode" singletontag="Two">
                      <property name="orientation" action="default">Axial</property>
                      <property name="viewlabel" action="default">2</property>
                    </view>
                  </item>
                </layout>
              </item>
              <item>
                <layout type="vertical" split="true">
                  <item>
                    <view class="vtkMRMLSliceNode" singletontag="Three">
                      <property name="orientation" action="default">Axial</property>
                      <property name="viewlabel" action="default">3</property>
                    </view>
                  </item>
                  <item>
                    <view class="vtkMRMLSliceNode" singletontag="Four">
                      <property name="orientation" action="default">Axial</property>
                      <property name="viewlabel" action="default">4</property>
                    </view>
                  </item>
                </layout>
              </item>
            </layout>
            '''
            layoutNode.AddLayoutDescription(customLayoutId, customLayout)
            lm.setLayout(customLayoutId)

            # Label overlays and defaults
            for tag, label in (("One", "1"), ("Two", "2"), ("Three", "3"), ("Four", "4")):
                sw = lm.sliceWidget(tag)
                if sw:
                    sn = sw.mrmlSliceNode()
                    if sn:
                        sn.SetLayoutLabel(label)
                        sn.SetOrientationToAxial()
                        sn.SetSliceVisible(True)

    ensure_2x2_layout()

    # Locate an existing SequenceBrowser
    browsers = list(slicer.util.getNodesByClass("vtkMRMLSequenceBrowserNode"))
    if not browsers:
        raise RuntimeError("未找到序列浏览器（SequenceBrowserNode）。请先加载序列并创建浏览器。")

    # Choose the first browser with a valid master sequence that has >= 2 items
    browser1 = None
    seq = None
    for b in browsers:
        s = b.GetMasterSequenceNode()
        if s and s.GetNumberOfDataNodes() >= 2:
            browser1 = b
            seq = s
            break

    if browser1 is None or seq is None:
        raise RuntimeError("未找到包含至少2帧的主序列。")

    sequencesLogic = slicer.modules.sequences.logic()

    # Ensure proxy for browser1 (frame1)
    proxy1 = browser1.GetProxyNode(seq)
    if proxy1 is None:
        proxy1 = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode", "SequenceProxy_Frame1")
        sequencesLogic.AddSynchronizedNode(proxy1, seq, browser1)

    # Find or create a second browser bound to the same sequence (frame2)
    browser2 = None
    for b in browsers:
        if b is browser1:
            continue
        if b.GetMasterSequenceNodeID() == seq.GetID():
            browser2 = b
            break
    if browser2 is None:
        browser2 = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSequenceBrowserNode", "SequenceBrowser_Frame2")
        browser2.SetAndObserveMasterSequenceNodeID(seq.GetID())

    # Ensure proxy for browser2
    proxy2 = browser2.GetProxyNode(seq)
    if proxy2 is None:
        baseName = proxy1.GetName() if proxy1 else (seq.GetName() or "Sequence")
        proxy2 = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode", f"{baseName}_Frame2")
        sequencesLogic.AddSynchronizedNode(proxy2, seq, browser2)

    # Select frames
    browser1.SetSelectedItemNumber(frame1_index)  # frame 1
    browser2.SetSelectedItemNumber(frame2_index)  # frame 2

    # Map views and orientations
    mapping = [
        ("One", "Axial", proxy1),     # Slice 1: Axial frame 1
        ("Two", "Sagittal", proxy1),  # Slice 2: Sagittal frame 1
        ("Three", "Axial", proxy2),   # Slice 3: Axial frame 2
        ("Four", "Sagittal", proxy2), # Slice 4: Sagittal frame 2
    ]

    for tag, orientation, vol in mapping:
        sw = lm.sliceWidget(tag)
        if sw is None:
            continue
        sn = sw.mrmlSliceNode()
        scn = sw.mrmlSliceCompositeNode()

        # Orientation
        ol = orientation.lower()
        if ol.startswith("ax"):
            sn.SetOrientationToAxial()
        elif ol.startswith("sag"):
            sn.SetOrientationToSagittal()
        elif ol.startswith("cor"):
            sn.SetOrientationToCoronal()

        # Set background to the proxy volume for the selected frame
        if vol:
            scn.SetBackgroundVolumeID(vol.GetID())

        # Fit to content
        sw.sliceLogic().FitSliceToAll()

    print("Configured 2x2 sequence views: [1 Axial f1, 2 Sagittal f1, 3 Axial f2, 4 Sagittal f2]")


if __name__ == "__main__":
    try:
        configure_sequence_2x2_views()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"ERROR: {e}")
