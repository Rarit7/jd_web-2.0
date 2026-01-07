// 自定义 ECharts 按需引入配置
// 只导入项目中实际使用的组件,实现 tree-shaking

import * as echarts from 'echarts/core'

// 导入图表类型
import {
  BarChart,
  LineChart,
  PieChart,
  FunnelChart,
  ScatterChart,
  MapChart,
} from 'echarts/charts'

// 导入组件
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  GeoComponent,
  ToolboxComponent,
  VisualMapComponent,
} from 'echarts/components'

// 导入渲染器
import { CanvasRenderer } from 'echarts/renderers'

// 注册必需的组件
echarts.use([
  // 图表类型
  BarChart,
  LineChart,
  PieChart,
  FunnelChart,
  ScatterChart,
  MapChart,

  // 组件
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  GeoComponent,
  ToolboxComponent,
  VisualMapComponent,

  // 渲染器
  CanvasRenderer,
])

// 导出配置好的 echarts 实例
export default echarts
