"""
Apply a 2x2 slice-only layout in 3D Slicer with views labeled 1,2,3,4
from top-to-bottom, left-to-right.

Usage:
- Open this file and copy-paste its entire content into Slicer's Python Interactor, hit Enter.
- Or in the Interactor: exec(open(r'<path-to-this-file>').read())
"""


def set_2x2_slice_layout():
    import slicer

    lm = slicer.app.layoutManager()
    layoutNode = lm.layoutLogic().GetLayoutNode()

    customLayoutId = 556  # arbitrary unique id

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

    # Register and apply layout
    layoutNode.AddLayoutDescription(customLayoutId, customLayout)
    lm.setLayout(customLayoutId)

    # Ensure labels are shown as 1..4 and set default properties
    tagLabelPairs = [("One", "1"), ("Two", "2"), ("Three", "3"), ("Four", "4")]
    for tag, label in tagLabelPairs:
        sw = lm.sliceWidget(tag)
        if sw:
            sn = sw.mrmlSliceNode()
            if sn:
                # Label in corner overlay
                sn.SetLayoutLabel(label)
                # Default to Axial for all (can be changed later if needed)
                sn.SetOrientationToAxial()
                # Make slice visible
                sn.SetSliceVisible(True)

    print("Applied 2x2 slice layout (labels 1-4: top-to-bottom, left-to-right).")


if __name__ == "__main__":
    try:
        set_2x2_slice_layout()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"ERROR: {e}")
