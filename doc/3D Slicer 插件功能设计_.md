

# **TAVR-Analytics Workflow 插件：产品需求与功能设计文档**

## **第一部分：战略概述与工作流设计**

### **1.1. 临床挑战：TAVR术后评估的低效性与数据碎片化**

经导管主动脉瓣置换术（Transcatheter Aortic Valve Replacement, TAVR）作为一种微创治疗严重主动脉瓣狭窄（AS）的革命性技术，已在临床广泛应用，并逐渐扩展至中低风险及更年轻的患者群体 1。随着患者生存期的延长，对植入生物瓣膜的长期耐久性和术后并发症的评估变得至关重要。当前，TAVR术后评估工作流面临两大核心挑战：效率低下和数据割裂。

临床医生通常依赖专用的商业软件（如3mensio）对术后4D心脏CT影像进行复杂的测量分析 1。这一过程本身需要专业技能和大量时间。完成测量后，医生需要将数十个关键参数，如瓣膜植入深度、支架形态、瓣叶增厚（HALT）、瓣叶活动度减退（RELM）等，手动转录到一份标准化的评估报告表单中 1。这个流程存在显著的弊端：

1. **操作环境割裂**：测量分析和报告填写在两个完全独立的软件环境中进行，增加了医生的工作负担和操作的复杂性。  
2. **数据转录风险**：手动抄录数据极易引入人为错误，可能导致评估结果失真，影响临床决策的准确性。  
3. **效率瓶颈**：整个流程耗时较长，成为临床科研和患者随访工作中的主要瓶颈，限制了对大量病例进行系统性分析的能力。  
4. **数据追溯困难**：最终的表单报告与原始的影像测量过程分离，当需要复核或追溯某个特定数据的来源时，操作十分繁琐，不利于质量控制和研究的严谨性。

因此，开发一个集成化的解决方案，将数据分析与报告生成整合在统一平台内，是解决当前临床痛点、提升TAVR术后评估质量与效率的关键。

### **1.2. 插件解决方案：3D Slicer内的集成化TAVR分析环境**

为应对上述挑战，本报告提出设计并开发一款名为“TAVR-Analytics Workflow”的插件，该插件将内嵌于功能强大且开源的医学影像平台3D Slicer中 2。此解决方案的核心价值在于提供一个“单一窗口”式的集成化环境，将TAVR术后评估的全流程——从数据导入、四维可视化、半自动分割、引导式测量到自动化报告生成——无缝整合。

该插件的开发不仅是现有手动流程的简单自动化，更是一次临床分析能力的升级。通过自动化计算，插件能够精确量化一系列对患者长期预后至关重要的影像学指标。例如，研究已明确指出，瓣膜相关亚临床血栓事件（Prosthetic-associated subclinical thrombotic events, PASTE）是影响瓣膜长期耐久性的关键因素 1。其中，低密度瓣叶增厚（HALT）和瓣叶活动度减退（RELM）被认为是亚临床瓣叶血栓（SLT）的核心影像学特征，直接关系到瓣膜功能 1。更重要的是，窦内充盈缺损（Sinus Filling Defect, SFD）已被证实是主要不良心血管复合事件（MACCO）的独立预测因子，对患者的长期生存和生活质量有直接影响 1。

当前的手动流程使得对这些前沿指标的评估费时费力，难以普及。本插件通过将这些复杂分析标准化、自动化，极大地降低了技术门槛，提高了评估的可重复性和效率。这使得临床医生能够更便捷、更系统地对患者进行风险分层，从而可能更早地介入治疗（如调整抗凝方案），以期改善患者的长期预后 1。因此，该插件不仅是一个效率工具，更是一个推动临床实践进步、提升患者管理水平的先进分析平台。

### **1.3. 自动化工作流设计**

为了直观地展示本插件带来的流程优化，下面将对比当前的手动工作流（As-Is）与插件实现的自动化工作流（To-Be）。

**当前手动工作流 (As-Is):**

在3mensio中加载CT数据 → 进行复杂的手动测量 → 生成3mensio可视化报告 → 打开独立的Word/Excel表单 → 手动查找并转录数十个数据点 → 完成最终报告

**插件自动化工作流 (To-Be):**

在Slicer插件中加载4D CT数据 → 执行引导式分割与标志点放置 → 一键运行自动化分析 → 在交互式控制台审核并验证结果 → 生成包含数据与图像的最终PDF报告

这一流程的重构，将原本分散、耗时、易错的多步骤操作，转变为一个线性的、高度自动化的、在单一平台内即可完成的闭环任务。这不仅极大地解放了临床医生的生产力，也为TAVR术后评估的标准化和规模化研究奠定了坚实的技术基础。

## **第二部分：模块一 \- 数据导入与场景准备**

本模块是整个工作流的起点，负责将原始的临床影像数据安全、准确地导入3D Slicer环境，并为后续的精细化分析做好准备。其核心功能包括4D数据序列的正确加载、患者基本信息的自动填充以及关键心动周期的管理。

### **2.1. 数据加载与验证**

**功能需求**：插件需要在3D Slicer的主工具栏中提供一个专属的启动按钮。点击后，将弹出一个专门用于数据加载的用户界面（UI）。

**数据加载机制**：

* **输入格式**：插件的主要输入是包含TAVR术后随访信息的4D心脏CT DICOM序列。它将利用3D Slicer强大的原生DICOM解析能力，将这一时间序列数据作为“Volume Sequence”加载到场景中 3。选择  
  Volume Sequence格式至关重要，因为它完整地保留了各三维容积数据之间的时间对应关系（即心动周期时相），这是后续进行动态评估（如RELM分析）的根本前提。  
* **兼容性**：插件应能处理来自不同CT厂商的DICOM数据，并能正确解析其时间序列信息。

**信息自动预填充**：

* **DICOM元数据解析**：在DICOM序列成功加载后，插件将自动执行脚本，读取关键的DICOM标签，例如 (0010,0010) Patient's Name、(0010,0020) Patient ID、(0010,0030) Patient's Birth Date 和 (0008,0020) Study Date 等。  
* **数据映射**：解析出的信息将被自动填充到插件内部数据模型的对应字段中。该数据模型在结构上完全仿照最终报告表单“杭州方案术后CT核心实验室评估表”的第一部分“基本情况” 1。这将预先填好受试者编号、年龄、性别、手术时间、CT扫描时间等基础信息。

**用户交互界面**：

* **数据确认**：UI将清晰地展示已加载的序列信息和自动填充的患者数据，供用户进行最终确认。  
* **手动编辑**：所有自动填充的字段均应支持手动编辑，以应对DICOM信息不完整或错误等特殊情况。  
* **关键信息输入**：UI中将设置醒目的下拉菜单或输入框，要求用户必须选择或输入“瓣膜品牌”（Valve Brand）和“瓣膜型号”（Valve Model）。此项输入为强制性，因为后续的解剖平面重建和部分测量算法高度依赖于所植入瓣膜的具体型号 1。

### **2.2. 心动周期管理**

**功能需求**：TAVR术后分析中的多项关键测量，如瓣叶增厚（HALT）、瓣叶活动度减退（RELM）以及支架形态评估，必须在特定的心动周期时相上进行 1。因此，插件必须提供一个直观、精确的心动周期管理工具。

**核心组件：“心动周期时间轴”**：

* **可视化滑块**：插件界面将包含一个视觉化的滑块（Slider）控件，代表已加载的Volume Sequence的完整时间轴。该滑块的范围通常表示为R-R间期的百分比（例如，0% 到 100%）。  
* **实时视图更新**：当用户拖动或点击时间轴滑块时，3D Slicer的2D切片视图（Axial, Sagittal, Coronal）和3D视图将实时同步更新，动态展示心脏和瓣膜在整个心动周期中的运动过程 5。这为用户准确识别特定时相提供了直观的视觉反馈。

**用户交互流程**：

1. **时相识别与标记**：工作流将引导用户识别并标记出对于后续分析至关重要的几个心动周期时相。UI上将提供明确的功能按钮，如“标记舒张末期 (Mark End-Diastole)”和“标记收缩末期 (Mark End-Systole)”。  
2. **标记操作**：用户通过拖动时间轴，在视图中找到心室舒张最充分（通常瓣叶处于闭合或半闭合状态）的帧，然后点击“标记舒张末期”按钮。同理，找到心室收缩最剧烈（瓣叶开放最大）的帧，点击“标记收缩末期”按钮。  
3. **时相与测量的自动关联**：插件内部会将这些用户标记的时相与特定的测量任务进行绑定。例如，根据临床研究规范，“HALT的评估应在心脏舒张期进行” 1。因此，当用户进入HALT分析模块时，插件将自动切换到用户标记的“舒张末期”时相。同样，RELM的分析将默认在“收缩末期”进行。  
4. **精确时相记录**：在提供的3mensio报告样本中，可以看到测量是在具体的时相百分比（如 28.0% 和 73.0%）进行的 1。最终的评估表单也要求填写每个测量的“测量期相 %” 1。因此，当用户标记一个时相时，插件会记录下该帧对应的精确百分比。这个百分比将与所有在该时相下进行的测量结果一同存储，并最终呈现在报告中，确保了评估过程的精确性和可追溯性。这一设计确保了插件不仅执行测量，还忠实记录了测量的上下文，这对于高质量的临床研究至关重要。

## **第三部分：模块二 \- 引导式分割与解剖标志点定义**

在完成数据导入和时相准备后，工作流进入核心的几何建模阶段。本模块的目标是创建TAVR瓣膜、主动脉根部及相关结构的高精度三维模型，并定义关键的解剖标志点。这些模型和点是所有后续自动化测量的基础。

### **3.1. 核心分割引擎**

**功能需求**：为了进行精确的几何测量，必须先从CT容积数据中准确地分割出（即描绘出轮廓）主动脉根部、主动脉腔以及TAVR瓣膜支架的3D形态。

**分割策略（半自动化）**：考虑到临床应用的鲁棒性和准确性，初期版本将采用一套基于3D Slicer原生Segment Editor模块的、由用户引导的半自动化分割流程。插件将通过Python脚本调用并控制Segment Editor的各种效果（effects），为用户提供一个简化的、任务导向的UI 6。

1. **瓣膜支架分割**：  
   * **方法**：利用Threshold（阈值）效果。TAVR瓣膜的金属支架在CT图像上呈现极高的亨氏单位（HU）值，与周围的软组织和血液形成鲜明对比。  
   * **流程**：插件将自动建议一个较高的HU值范围（例如，800 HU以上），并实时预览分割结果。用户可以微调阈值范围，以确保完整、准确地捕获整个支架结构，同时排除周围的钙化斑块。  
2. **主动脉根部与腔内分割**：  
   * **方法**：采用Grow from Seeds（种子点增长）效果，这是一种强大且直观的交互式分割方法 9。  
   * **流程**：插件将引导用户执行以下操作：  
     * **放置前景种子**：在Segment Editor中选择为“主动脉”创建的分割区，使用Paint（画笔）工具在主动脉腔内的几个不同位置（如主动脉窦、升主动脉）涂抹几笔。这些笔触作为“种子”，告诉算法这些区域确定无疑是主动脉。  
     * **放置背景种子**：选择为“背景”或“非主动脉”创建的分割区，在主动脉周围但具有相似CT值的结构上（如左心室、右心室、肺动脉）进行涂抹。这些背景种子能够有效防止分割算法“泄漏”到邻近的解剖结构中。  
   * **执行与修正**：用户放置好种子点后，点击插件UI上的“执行分割”按钮。算法将从前景种子点开始生长，直到遇到背景种子点或图像梯度变化剧烈的边界。用户可以实时预览3D分割结果，并根据需要添加更多的前景或背景种子点来迭代优化分割的精度。

**未来扩展性**：本插件的架构设计将保持模块化。分割引擎部分将被设计成一个可替换的组件。这为未来集成更先进的全自动分割技术（如基于U-Net的深度学习模型）预留了接口 10。当有稳定可靠的AI模型可用时，可以无缝替换或补充现有的半自动流程，实现一键式全自动分割。

### **3.2. 解剖平面重建**

**功能需求**：评估表单 1 和3mensio报告 1 中的大量测量均基于特定的解剖参考平面。插件必须能够精确地重建这些平面。

**平面重建算法**：

1. **原生主动脉瓣环平面 (Native Annulus Plane)**：  
   * **定义**：这是评估瓣膜植入深度的黄金标准参考平面。它由三个原生主动脉瓣尖的最低点（nadir）所定义。  
   * **流程**：插件将进入一个引导式工作流，要求用户在CT图像上（通常是舒张末期）通过点击放置三个vtkMRMLMarkupsFiducialNode（基准点），分别对应左冠瓣、右冠瓣和无冠瓣的瓣尖最低点。  
   * **计算**：获取这三个点的3D坐标后，插件将调用VTK库中的算法来计算通过这三点的最佳拟合平面 16。该平面的方程（法向量和原点）将被存储，作为后续深度测量的基准。  
2. **瓣膜支架相关平面 (Inflow, Nadir, Commissure Level)**：  
   * **核心挑战与设计**：此处存在一个关键的、非显而易见的技术要求。评估表单 1 的脚注“各瓣膜测量对照点”明确指出了不同品牌和型号的瓣膜，其关键测量平面的定义方式完全不同。例如，Medtronic Evolut的  
     nadir level（瓣叶窦底平面）定义在“1.5个菱形格”处，而Edwards SAPIEN3则定义在“底部往上0.5个菱形格”处。  
   * **解决方案**：这直接决定了插件必须采用“瓣膜特异性”的设计。在模块一中用户选择的“瓣膜型号”将成为此处算法的关键输入。插件内部必须包含一个逻辑判断结构（if-elif-else），根据所选瓣膜型号，调用相应的平面定义规则。  
   * **算法实现**：  
     * 首先，通过图像处理算法分析瓣膜支架的3D分割模型，自动识别其底部边缘作为“0”参考点。  
     * 然后，根据所选瓣膜的规则，沿支架中心线向上计算相应的距离或识别特定的结构特征（如“菱形格”）。这可能需要结合图像处理技术来识别支架网格的周期性结构。  
     * 在计算出的高度位置，定义出inflow plane（流入道平面）、nadir plane（瓣叶窦底平面）和commissure level plane（瓣叶对合平面）。

### **3.3. 交互式标志点放置**

**功能需求**：评估连合对齐和冠脉风险需要几个关键解剖结构的确切三维坐标。

**交互式工作流**：插件将提供一个专门的“标志点放置”步骤。在此步骤中，用户界面会清晰地提示用户需要放置哪些点。用户将在2D和3D视图的联动下，使用鼠标点击来放置vtkMRMLMarkupsFiducialNode基准点 18。需要定义的标志点包括：

* 三个**原生主动脉瓣连合** (Native Aortic Commissures) 的位置（如果术后CT仍清晰可见）。  
* 三个TAVR**人工瓣膜的新连合** (Neo-commissures) 的位置。  
* **左冠状动脉开口** (Left Coronary Artery Ostium, LCA) 的中心点。  
* **右冠状动脉开口** (Right Coronary Artery Ostium, RCA) 的中心点。

这些精确标记的点将作为输入，用于第四部分模块中的角度和距离计算。

### **表1：不同型号瓣膜测量平面定义**

为了确保开发团队能够准确实现瓣膜特异性的平面重建逻辑，下表将评估表单 1 中的文字描述规则，转化为结构化的技术规格。此表是本模块开发的核心参考。

| 瓣膜型号 (Valve Model) | 流入道平面 (Inflow Plane) 定义 | 瓣叶窦底平面 (Nadir Plane) 定义 | 瓣叶对合平面 (Commissure Level) 定义 |
| :---- | :---- | :---- | :---- |
| **美敦力 (Medtronic) Evolut R/PRO** | 支架最底部至半个菱形格之间的直筒状区域 | 从底部向上1.5个菱形格高度 | 从底部向上3个菱形格高度 |
| **爱德华 (Edwards) SAPIEN3** | (无需填写，该型号使用外裙边平面) | 从底部向上0.5个菱形格高度 | 从顶部向下0.5个菱形格高度 |
| **启明 (Venus) Venus/VenusA** | 支架底部半个菱形格高度 | 从底部向上1.5个菱形格高度 | 从底部向上3个菱形格高度 |
| **微创 (MicroPort) Vitaflow** | 支架最底部 | 从底部向上1个菱形格高度 | 从底部向上2个菱形格高度（两点完全汇合处） |
| **沛佳 (Peijia) Taurus** | 支架最底部 | 从底部向上半个菱形格高度 | 从底部向上2.5个菱形格高度 |
| **(其他型号)** | (根据未来需求可扩展) | (根据未来需求可扩展) | (根据未来需求可扩展) |

注：对于SAPIEN3，评估表单 1 特别要求测量“外裙边平面 (outerskirt plane)”，其定义为“从底部向上1个菱形格高度”。插件需实现对此特殊平面的支持。

## **第四部分：模块三 \- 自动化测量与量化分析**

本模块是插件的核心计算引擎。它利用前一模块生成的3D分割模型、解剖平面和标志点，自动执行所有必需的量化分析，并直接填充评估表单 1 中定义的各项参数。

### **4.1. 瓣膜支架几何形态与植入位置评估**

**支架框架尺寸测量**：

* **算法流程**：对于在模块三中重建的每一个关键平面（inflow, nadir, commissure level等），插件将自动执行以下操作：  
  1. 计算该平面与瓣膜支架3D分割模型的交集，生成一个2D闭合轮廓。  
  2. 对这个2D轮廓，使用几何计算库（如VTK）精确计算其：  
     * 周长 (Perimeter)，单位：mm。  
     * 面积 (Area)，单位：mm²。  
     * 最长径 (Longest Diameter)，单位：mm。  
     * 最短径 (Shortest Diameter)，单位：mm。  
     * 周长平均径 (Perimeter-derived Diameter)，计算公式为 Dperimeter​=P/π。  
     * 面积平均径 (Area-derived Diameter)，计算公式为 Darea​=2×A/π​。  
* **数据输出**：所有计算结果将直接、准确地填充到评估表单 1 中“三、人工瓣膜支架评估”部分的对应字段。

**植入深度测量**：

* **算法流程**：  
  1. **输入**：需要模块三中定义的“原生主动脉瓣环平面”以及TAVR瓣膜的3D分割模型。  
  2. **瓣尖识别**：用户将被引导在瓣膜模型上交互式地点击或通过图像处理算法自动识别出三个TAVR瓣叶的最低点（nadir）的三维坐标。  
  3. **距离计算**：对于每个瓣尖（无冠NC, 左冠LC, 右冠RC），插件将计算该点到“原生主动脉瓣环平面”的垂直（最短）距离。这是一个标准的点到平面距离计算问题，可通过向量投影或专用几何函数库解决 21。  
* **数据输出**：计算出的三个深度值（NC mm, LC mm, RC mm）将填充到评估表单 1 中“瓣膜植入深度”部分的对应字段。

### **4.2. 连合对齐与冠脉风险分析**

**连合对齐角度计算**：

* **算法流程**：  
  1. **输入**：需要模块三中用户放置的“原生主动脉瓣连合”和“人工瓣膜新连合”的标志点坐标。  
  2. **中心点定义**：计算主动脉瓣环的几何中心点。  
  3. **向量构建**：以瓣环中心点为起点，分别构建指向每个原生连合点和每个新连合点的三维向量。  
  4. **角度计算**：使用标准向量数学库，计算每对对应的原生-新连合向量之间的夹角 25。例如，计算原生  
     LCC/NCC连合向量与最接近的新连合向量之间的角度。  
* **数据输出**：根据评估表单 1 的“交接对齐 (commissure alignment)”部分，计算并填入  
  Angle RCA to RCC/LCC commissure等六个角度值。

### **4.3. 瓣膜相关亚临床血栓事件（PASTE）分析**

本子模块是插件的高级功能核心，旨在实现对HALT、RELM、SFD和PFD等关键预后指标的标准化评估 1。

**HALT (低密度瓣叶增厚) 分析**：

* **UI与工作流**：插件将提供一个专门的HALT分析界面。启动后，视图将自动锁定到用户在模块一中标记的“舒张末期”时相。  
* **用户交互**：用户首先从下拉菜单中选择要评估的瓣叶（LC, RC, 或 NC）。然后，使用Segment Editor中的Paint或Draw工具，在2D切片视图上仔细地“涂抹”出瓣叶上呈现低密度增厚的区域。  
* **自动化计算**：在用户完成涂抹后，插件将：  
  1. 获取这个新创建的“HALT区域”子分割。  
  2. 访问该子分割所包含的体素数据 29，并计算其最大厚度（通过局部厚度算法）和面积。  
  3. 自动计算该HALT区域面积占整个瓣叶总面积的百分比。  
  4. 根据评估表单 1 中定义的分级标准（  
     ≤25%, 25-50%, 50%-75%, ＞75%），自动为该瓣叶选择对应的HALT分级。

**RELM (瓣叶活动度减退) 分析**：

* **UI与工作流**：启动RELM分析工具后，视图将在用户标记的“舒张末期”和“收缩末期”之间切换，以便于动态观察。  
* **自动化计算**：插件将严格按照评估表单 1 中提供的公式  
  RELM=W/(1/2×D) 进行计算：  
  * W (增厚瓣叶宽度)：直接采用上一步HALT分析中测得的增厚区域宽度。  
  * D (同平面支架内径)：自动测量在同一解剖平面上，瓣膜支架分割模型的内径。  
  * 插件将自动计算出RELM百分比，并根据研究文献 1 中定义的分级标准（轻度:  
    \<50%, 中度: \>50%, \<70%, 重度: ≥70%）和表单中的选项（轻度, 中度, 重度, 瓣叶不活动），自动为该瓣叶选择对应的RELM分级。

**SFD (窦内充盈缺损) 与 PFD (瓣叶下充盈缺损) 分析**：

* **UI设计**：提供一个简洁的用户界面，包含SFD和PFD两个评估项。每项都有一组复选框：无 (None), 有 (Present), 难以判定 (Indeterminate)。  
* **用户交互**：  
  * **SFD**：如果用户勾选“有 (Present)”，则下方用于指定受累主动脉窦的复选框（LC, RC, NC）将被激活，用户可多选 1。  
  * **PFD**：如果用户勾选“有 (Present)”，插件将激活一个简易的测量工具，提示用户在2D视图上点击充盈缺损最厚的位置，以交互方式测量其最大厚度（mm）。

### **表2：核心测量参数列表**

此表是整个插件功能的技术核心蓝图，它将评估表单中的每一个字段，都精确映射到插件内部的输入源和计算方法。这是确保功能完整性、指导开发和测试的关键文档。

| 报告字段名 (Report Field Name) | 所属报告部分 (Report Section) | 计算所需输入 (Required Inputs) | 算法描述 (Algorithmic Description) | 单位 (Unit) |
| :---- | :---- | :---- | :---- | :---- |
| **受试者编号** | 一、基本情况 | DICOM数据 | 从DICOM Tag (0010,0020) 自动读取 | N/A |
| **年龄** | 一、基本情况 | DICOM数据 | 从出生日期 (0010,0030) 和研究日期 (0008,0020) 计算 | 岁 |
| **HALT分级: LC** | 二、人工瓣膜瓣叶评估 | 舒张末期时相, LC瓣叶上的HALT分割区 | 计算HALT分割区面积与LC瓣叶总面积之比，按标准分级 | ≤25%... |
| **RELM分级: RC** | 二、人工瓣膜瓣叶评估 | RC瓣叶HALT宽度(W), 同平面支架内径(D) | 计算 W / (0.5 \* D)，按标准分级 | 轻/中/重度 |
| **SFD: 受累主动脉窦** | 二、人工瓣膜瓣叶评估 | 用户勾选 | 记录用户在UI上的选择 | LC/RC/NC |
| **PFD: 最大的充盈缺损厚度** | 二、人工瓣膜瓣叶评估 | 用户交互测量 | 记录用户使用测量工具测得的距离值 | mm |
| **支架瓣叶窦底平面 周长** | 三、人工瓣膜支架评估 | 支架分割模型, 窦底平面 | 计算支架模型与窦底平面交线的周长 | mm |
| **支架瓣叶窦底平面 面积** | 三、人工瓣膜支架评估 | 支架分割模型, 窦底平面 | 计算支架模型与窦底平面交线所围成区域的面积 | mm² |
| **支架瓣叶窦底平面 最长径** | 三、人工瓣膜支架评估 | 支架分割模型, 窦底平面 | 计算交线轮廓上的最大费雷特直径 | mm |
| **植入深度: NC** | 三、人工瓣膜支架评估 | NC瓣尖最低点坐标, 原生瓣环平面 | 计算点到平面的垂直距离 | mm |
| **交接对齐: Angle RCA to LCC/NCC** | 四、交接对齐 | 瓣环中心, RCA, LCC/NCC原生连合, 新连合坐标 | 计算原生连合向量与新连合向量之间的夹角 | ° |

## **第五部分：模块四 \- 交互式审核与报告生成**

此模块是工作流的最后环节，旨在将所有自动化计算的结果以一种清晰、可信、可交互的方式呈现给临床医生，并最终生成一份符合临床和科研标准的、图文并茂的PDF报告。

### **5.1. 交互式审核控制台**

**功能需求**：在生成最终报告之前，必须为临床医生提供一个全面审核所有数据的机会，并赋予其验证、修正和否决任何自动化结果的权力。这是建立用户信任、确保临床准确性的核心。

**UI设计与功能**：

* **持久化侧边栏**：插件的主界面将包含一个持久化的侧边栏，该侧边栏以一个可编辑的、分层树状结构，完整复现评估表单 1 的所有字段和层级。  
* **动态数据显示**：随着前序模块中各项测量的完成，该侧边栏中的对应字段将被实时、动态地填充上计算结果。  
* **核心交互功能——“所点即所见”**：  
  * **测量值与视图联动**：当用户在审核控制台中点击任何一个测量值字段时（例如，点击“流入道平面”的“最长径”），3D Slicer的2D和3D视图将自动执行一系列操作：跳转到进行该测量的正确心动周期时相，并调整相机视角，将视图中心聚焦于该测量的解剖位置。  
  * **可视化叠加**：同时，在视图上将出现一个临时的视觉叠加层（overlay），用图形化的方式清晰地展示该测量的具体内容。例如，如果点击的是“最长径”，视图中将高亮显示流入道平面的轮廓，并绘制出代表最长径的线条。这种设计灵感来源于3Dmensio报告的直观性 1，它将抽象的数据与具体的解剖结构联系起来，极大地提升了结果的可解释性和可信度。实现此功能需要通过Python脚本精确控制Slicer的视图控制器和渲染管线，以添加和管理这些视觉叠加元素 33。  
* **数据可编辑性与溯源**：  
  * 所有在控制台中显示的数值字段都应是可编辑的。这允许医生在发现自动化结果有偏差时，根据其专业判断进行手动修正。  
  * 为了保持数据的完整性和可追溯性，任何被用户手动修改过的数值，在最终生成的报告中都将被特殊标记（例如，以星号\*或不同颜色字体显示），并可能在附注中说明“由用户手动修正”。

### **5.2. 自动化报告生成器**

**功能需求**：工作流的最终产物必须是一个独立的、易于分享和归档的PDF文档。该文档不仅要包含所有评估数据，还需提供关键的影像学证据，并严格遵循指定的格式。

**PDF生成技术**：

* **触发机制**：在交互式审核控制台下方，将设置一个醒目的“生成报告 (Generate Report)”按钮。点击此按钮将启动最终的报告合成程序。  
* **后端库选择**：插件将集成一个成熟的Python PDF生成库，如 **FPDF2** 或 **ReportLab** 37。选择这些库的原因在于它们不依赖外部应用，功能强大，支持复杂的表格布局、中文字符集以及高质量的图像嵌入，能够完全满足本项目的需求。

**报告内容与版式**：

1. **格式精确复制**：生成的PDF文档的第一页或主体部分，将在版式、字体、表格结构和文本内容上，完全复刻“杭州方案术后CT核心实验室评估表” 1 的外观。  
2. **数据自动填充**：所有在交互式审核控制台中最终确认的数据，将被精确无误地填入PDF表单的相应位置。

**图文并茂的增强型报告**：

* **设计理念**：单纯的数据表单 1 虽然信息密集，但缺乏视觉上下文；而3mensio的截图报告 1 虽然直观，但数据结构化不足。一个理想的临床报告应当兼具二者之长。  
* **实现方法**：在用户点击“生成报告”时，插件不仅会填充数据，还会执行一个自动化的“影像取证”脚本。该脚本会根据报告内容，程序化地重现关键的测量场景并进行截图：  
  * **HALT/RELM**：自动跳转到舒张末期，高亮显示用户绘制的HALT区域，并截图。  
  * **植入深度**：自动显示原生瓣环平面和瓣尖最低点，并绘制表示垂直距离的测量线，然后截图。  
  * **支架形态**：自动显示如瓣叶窦底平面的2D轮廓，并标注其最长径和最短径，然后截图。  
  * **连合对齐**：自动显示带有原生及新连合标志点的鸟瞰视图，并标注关键角度，然后截图。  
* **报告整合**：这些自动捕获并标注了测量值的截图，将被作为附录或第二页，嵌入到最终生成的PDF文档中。这将为报告中的每一个关键数据点提供直接的、不可否认的影像学证据，形成一份数据完整、视觉清晰、具有高度说服力和可审计性的综合性临床评估报告。

## **第六部分：结论与未来展望**

本产品需求与功能设计文档详细规划了一款旨在变革TAVR术后评估流程的3D Slicer插件——“TAVR-Analytics Workflow”。通过将数据加载、四维可视化、半自动分割、引导式测量和自动化报告生成等功能无缝集成于单一平台，该插件旨在解决当前临床工作流中存在的效率低下、数据割裂和潜在人为错误等核心痛点。

插件的核心价值不仅在于自动化，更在于其临床分析能力的深化。它将对HALT、RELM、SFD等前沿预后指标的量化评估变得标准化和高效化，这些指标已被证实与瓣膜耐久性及患者长期不良心血管事件密切相关 1。因此，本插件有望成为一个强大的临床决策支持和科研工具，帮助医生更精确地进行风险分层，从而优化患者的长期管理策略。

**未来展望**：

1. **全自动AI分割**：当前版本采用半自动分割以保证初期版本的鲁棒性。未来，随着心脏AI分割技术的发展，可以集成预训练的深度学习模型（如U-Net架构），实现对主动脉根部和瓣膜支架的一键式全自动分割，进一步提升工作效率 15。  
2. **血流动力学分析集成**：结合4D Flow MRI数据或CFD（计算流体动力学）模拟，插件可扩展至评估瓣膜区域的血流动力学参数，如壁面剪切应力、血流停滞区等，为血栓形成提供更深层次的机理分析。  
3. **多中心数据兼容与验证**：在插件成熟后，可开展多中心研究，验证其在不同设备、不同人群中的稳定性和准确性，并建立基于大规模、标准化数据的预后预测模型。  
4. **云端部署与协作**：探索将插件的核心算法部署于云端，实现跨机构的数据分析与协作，并为构建大型TAVR术后随访数据库提供技术支持。

综上所述，“TAVR-Analytics Workflow”插件项目具有明确的临床需求、清晰的技术路径和广阔的应用前景。通过本设计文档的指导，开发团队可以构建一个功能强大、用户友好且具有高度临床价值的软件工具，为TAVR领域的临床实践与科学研究做出实质性贡献。

#### **引用的著作**

1. 13244\_2024\_Article\_1681.pdf  
2. 3D Slicer image computing platform | 3D Slicer, 访问时间为 八月 4, 2025， [https://www.slicer.org/](https://www.slicer.org/)  
3. SlicerHeart: An open-source computing platform for cardiac image ..., 访问时间为 八月 4, 2025， [https://pmc.ncbi.nlm.nih.gov/articles/PMC9485637/](https://pmc.ncbi.nlm.nih.gov/articles/PMC9485637/)  
4. HEARTBEAT4D: An Open-source Toolbox for Turning 4D Cardiac CT into VR/AR \- PMC, 访问时间为 八月 4, 2025， [https://pmc.ncbi.nlm.nih.gov/articles/PMC9712868/](https://pmc.ncbi.nlm.nih.gov/articles/PMC9712868/)  
5. Modules:FourDImage-Documentation-3.6 \- Slicer Wiki, 访问时间为 八月 4, 2025， [https://www.slicer.org/wiki/Modules:FourDImage-Documentation-3.6](https://www.slicer.org/wiki/Modules:FourDImage-Documentation-3.6)  
6. Python Script for segment growing and Logical operations \- 3D Slicer Community, 访问时间为 八月 4, 2025， [https://discourse.slicer.org/t/python-script-for-segment-growing-and-logical-operations/10004](https://discourse.slicer.org/t/python-script-for-segment-growing-and-logical-operations/10004)  
7. Segment editor \- 3D Slicer documentation \- Read the Docs, 访问时间为 八月 4, 2025， [https://slicer.readthedocs.io/en/latest/developer\_guide/modules/segmenteditor.html](https://slicer.readthedocs.io/en/latest/developer_guide/modules/segmenteditor.html)  
8. Slicer/Modules/Scripted/SegmentEditor/SegmentEditor.py at main \- GitHub, 访问时间为 八月 4, 2025， [https://github.com/Slicer/Slicer/blob/main/Modules/Scripted/SegmentEditor/SegmentEditor.py](https://github.com/Slicer/Slicer/blob/main/Modules/Scripted/SegmentEditor/SegmentEditor.py)  
9. Overview | 3D Slicer segmentation recipes \- GitHub Pages, 访问时间为 八月 4, 2025， [https://lassoan.github.io/SlicerSegmentationRecipes/AortaMaskedGrowFromSeeds/](https://lassoan.github.io/SlicerSegmentationRecipes/AortaMaskedGrowFromSeeds/)  
10. A 3D Image Segmentation Study of U-Net on CT Images of the Human Aorta with Morphologically Diverse Anatomy \- bioRxiv, 访问时间为 八月 4, 2025， [https://www.biorxiv.org/content/10.1101/2024.10.02.616348v1.full.pdf](https://www.biorxiv.org/content/10.1101/2024.10.02.616348v1.full.pdf)  
11. Deep-Cardiac-Volumetric-Mesh (DeepCarve) \- GitHub, 访问时间为 八月 4, 2025， [https://github.com/danpak94/Deep-Cardiac-Volumetric-Mesh](https://github.com/danpak94/Deep-Cardiac-Volumetric-Mesh)  
12. numisveinsson/SeqSeg: Code for Sequential Segmentations \- GitHub, 访问时间为 八月 4, 2025， [https://github.com/numisveinsson/SeqSeg](https://github.com/numisveinsson/SeqSeg)  
13. mirthAI/CIS-UNet \- GitHub, 访问时间为 八月 4, 2025， [https://github.com/mirthAI/CIS-UNet](https://github.com/mirthAI/CIS-UNet)  
14. \[2507.15524\] RARE-UNet: Resolution-Aligned Routing Entry for Adaptive Medical Image Segmentation \- arXiv, 访问时间为 八月 4, 2025， [http://arxiv.org/abs/2507.15524](http://arxiv.org/abs/2507.15524)  
15. \[1505.04597\] U-Net: Convolutional Networks for Biomedical Image Segmentation \- arXiv, 访问时间为 八月 4, 2025， [https://arxiv.org/abs/1505.04597](https://arxiv.org/abs/1505.04597)  
16. Plane \- VTK Examples, 访问时间为 八月 4, 2025， [https://examples.vtk.org/site/Cxx/GeometricObjects/Plane/](https://examples.vtk.org/site/Cxx/GeometricObjects/Plane/)  
17. vtkPlane Class Reference \- VTK, 访问时间为 八月 4, 2025， [https://www.vtk.org/doc/nightly/html/classvtkPlane.html](https://www.vtk.org/doc/nightly/html/classvtkPlane.html)  
18. Script repository \- 3D Slicer documentation \- Read the Docs, 访问时间为 八月 4, 2025， [https://slicer.readthedocs.io/en/latest/developer\_guide/script\_repository.html](https://slicer.readthedocs.io/en/latest/developer_guide/script_repository.html)  
19. Obtaining Segmentations for Fiducials \- Support \- 3D Slicer Community, 访问时间为 八月 4, 2025， [https://discourse.slicer.org/t/obtaining-segmentations-for-fiducials/13407](https://discourse.slicer.org/t/obtaining-segmentations-for-fiducials/13407)  
20. Place fiducial at centroid of current slice \- Support \- 3D Slicer Community, 访问时间为 八月 4, 2025， [https://discourse.slicer.org/t/place-fiducial-at-centroid-of-current-slice/22169](https://discourse.slicer.org/t/place-fiducial-at-centroid-of-current-slice/22169)  
21. Distance from point to plane \- Math Insight, 访问时间为 八月 4, 2025， [https://mathinsight.org/distance\_point\_plane](https://mathinsight.org/distance_point_plane)  
22. Plane | vtk.js \- Kitware, Inc., 访问时间为 八月 4, 2025， [https://kitware.github.io/vtk-js/api/Common\_DataModel\_Plane.html](https://kitware.github.io/vtk-js/api/Common_DataModel_Plane.html)  
23. Distance between point and plane \- Support \- 3D Slicer Community, 访问时间为 八月 4, 2025， [https://discourse.slicer.org/t/distance-between-point-and-plane/22091](https://discourse.slicer.org/t/distance-between-point-and-plane/22091)  
24. Distance between point and a plane represented with $3$ points in $3D$ space \- Math Stack Exchange, 访问时间为 八月 4, 2025， [https://math.stackexchange.com/questions/2590359/distance-between-point-and-a-plane-represented-with-3-points-in-3d-space](https://math.stackexchange.com/questions/2590359/distance-between-point-and-a-plane-represented-with-3-points-in-3d-space)  
25. How to Compute the Angle Between Vectors Using Python \- GeeksforGeeks, 访问时间为 八月 4, 2025， [https://www.geeksforgeeks.org/python/how-to-compute-the-angle-between-vectors-using-python/](https://www.geeksforgeeks.org/python/how-to-compute-the-angle-between-vectors-using-python/)  
26. Calculating the Angle Between Two Vectors Using NumPy | by Hey Amit \- Medium, 访问时间为 八月 4, 2025， [https://medium.com/@heyamit10/calculating-the-angle-between-two-vectors-using-numpy-17e64256601c](https://medium.com/@heyamit10/calculating-the-angle-between-two-vectors-using-numpy-17e64256601c)  
27. Calculate angle between oriented bounding boxes \- Development \- 3D Slicer Community, 访问时间为 八月 4, 2025， [https://discourse.slicer.org/t/calculate-angle-between-oriented-bounding-boxes/15241](https://discourse.slicer.org/t/calculate-angle-between-oriented-bounding-boxes/15241)  
28. python code to calculate angle between three point using their 3D coordinates, 访问时间为 八月 4, 2025， [https://stackoverflow.com/questions/35176451/python-code-to-calculate-angle-between-three-point-using-their-3d-coordinates](https://stackoverflow.com/questions/35176451/python-code-to-calculate-angle-between-three-point-using-their-3d-coordinates)  
29. Developer Guide \- 3D Slicer documentation, 访问时间为 八月 4, 2025， [https://slicer.readthedocs.io/en/latest/developer\_guide/index.html](https://slicer.readthedocs.io/en/latest/developer_guide/index.html)  
30. Number of voxels dependent on HU value \- Support \- 3D Slicer Community, 访问时间为 八月 4, 2025， [https://discourse.slicer.org/t/number-of-voxels-dependent-on-hu-value/15317](https://discourse.slicer.org/t/number-of-voxels-dependent-on-hu-value/15317)  
31. Threshold min and max values \- Development \- 3D Slicer Community, 访问时间为 八月 4, 2025， [https://discourse.slicer.org/t/threshold-min-and-max-values/28643](https://discourse.slicer.org/t/threshold-min-and-max-values/28643)  
32. How to access and manipulate segmentation node as a numpy array? \- Development, 访问时间为 八月 4, 2025， [https://discourse.slicer.org/t/how-to-access-and-manipulate-segmentation-node-as-a-numpy-array/34110](https://discourse.slicer.org/t/how-to-access-and-manipulate-segmentation-node-as-a-numpy-array/34110)  
33. Developer Guide \- 3D Slicer documentation \- Read the Docs, 访问时间为 八月 4, 2025， [https://slicer.readthedocs.io/en/5.4/developer\_guide/](https://slicer.readthedocs.io/en/5.4/developer_guide/)  
34. How to programmatically add control points in slicer from a numpy array \- Development, 访问时间为 八月 4, 2025， [https://discourse.slicer.org/t/how-to-programmatically-add-control-points-in-slicer-from-a-numpy-array/28342](https://discourse.slicer.org/t/how-to-programmatically-add-control-points-in-slicer-from-a-numpy-array/28342)  
35. Tutorial 4 \- Overlay two images using 3D Slicer \- YouTube, 访问时间为 八月 4, 2025， [https://www.youtube.com/watch?v=kYuLT0P4L4Y](https://www.youtube.com/watch?v=kYuLT0P4L4Y)  
36. Overlaying a dot on the camera stream using plus server and slicer module, 访问时间为 八月 4, 2025， [https://discourse.slicer.org/t/overlaying-a-dot-on-the-camera-stream-using-plus-server-and-slicer-module/5318](https://discourse.slicer.org/t/overlaying-a-dot-on-the-camera-stream-using-plus-server-and-slicer-module/5318)  
37. How to Generate PDFs in Python: 8 Tools Compared (Updated for 2025\) \- Templated.io, 访问时间为 八月 4, 2025， [https://templated.io/blog/generate-pdfs-in-python-with-libraries/](https://templated.io/blog/generate-pdfs-in-python-with-libraries/)  
38. py-pdf/fpdf2: Simple PDF generation for Python \- GitHub, 访问时间为 八月 4, 2025， [https://github.com/py-pdf/fpdf2](https://github.com/py-pdf/fpdf2)  
39. Creating a Python Class for Generating PDF Tables from a Pandas DataFrame Using FPDF2 | by Mohindra Jain | Medium, 访问时间为 八月 4, 2025， [https://medium.com/@mahijain9211/creating-a-python-class-for-generating-pdf-tables-from-a-pandas-dataframe-using-fpdf2-c0eb4b88355c](https://medium.com/@mahijain9211/creating-a-python-class-for-generating-pdf-tables-from-a-pandas-dataframe-using-fpdf2-c0eb4b88355c)  
40. Top 10 Python PDF generation libraries (2025 edition) \- Nutrient SDK, 访问时间为 八月 4, 2025， [https://www.nutrient.io/blog/top-10-ways-to-generate-pdfs-in-python/](https://www.nutrient.io/blog/top-10-ways-to-generate-pdfs-in-python/)  
41. \[2507.16573\] Semantic Segmentation for Preoperative Planning in Transcatheter Aortic Valve Replacement \- arXiv, 访问时间为 八月 4, 2025， [http://arxiv.org/abs/2507.16573](http://arxiv.org/abs/2507.16573)  
42. Semantic Segmentation for Preoperative Planning in Transcatheter Aortic Valve Replacement \- arXiv, 访问时间为 八月 4, 2025， [http://arxiv.org/pdf/2507.16573](http://arxiv.org/pdf/2507.16573)