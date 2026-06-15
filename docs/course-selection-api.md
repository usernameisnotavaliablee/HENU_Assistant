# 河南大学选课接口记录

本文档整理自 `xk.henu.edu.cn` 选课页面的浏览器会话与 HAR 抓包，用于后续做只读查询、课表规划和人工确认型辅助工具。不要把 HAR 中的 `JSESSIONID`、学号、`params`、`token`、`timestamp` 固化到代码或文档里。

## 入口链路

选课系统依赖菜单与 iframe 上下文，直接打开学生页面可能返回 `无效访问请求`。

```text
GET /frame/homes.action
GET /frame/jw/teacherstudentmenu.jsp?menucode=S20202
GET /student/wsxk.zx.html?menucode=S2020202&bqflag=1
```

`teacherstudentmenu.jsp` 中的选课相关菜单：

| 菜单 | 页面 |
| --- | --- |
| 网上选课 | `/student/wsxk.zx.html?menucode=S2020202` |
| 退选 | `/student/wsxk.tx.nopre.html?menucode=S2020205` |
| 外年级/专业选课 | `/student/wsxk.wnjzyxk.html?menucode=S2020210` |

## 选课状态接口

### 查询选课轮次时间

```http
POST /jw/common/getWsxkTimeRange.action?xktype=2
Referer: /student/wsxk.zx.html?menucode=S2020202
X-Requested-With: XMLHttpRequest
```

常见字段：

| 字段 | 含义 |
| --- | --- |
| `isValidTimerange` | 当前是否在开放时间内 |
| `qssj` / `jssj` | 起止时间 |
| `lcid` | 选课轮次 ID |
| `lcmc` | 轮次名称 |
| `xn` / `xqM` | 学年、学期 |
| `nj` | 年级 |

抓包样例中第一轮次为 `2026-06-11 09:30` 至 `2026-06-13 22:00`，`xktype=2`，`xn=2026`，`xqM=0`，`nj=2025`。

### 查询课程范围下拉

```http
POST /frame/droplist/getDropLists.action
Content-Type: application/x-www-form-urlencoded; charset=UTF-8

comboBoxName=MsKcfw
paramValue=2
isYXB=0
isCDDW=0
isXQ=0
isDJKSLB=0
isZY=0
```

抓包中的课程范围：

| code | name |
| --- | --- |
| `zxbnj` | 主修(本年级/专业) |
| `zxggrx` | 主修(公共任选) |
| `fx` | 辅修 |
| `zxknj` | 主修(可跨年级/专业) |

### 查询已选学分/门数

```http
POST /jw/common/getSelectLessonScoreKcsInfo.action
Content-Type: application/x-www-form-urlencoded; charset=UTF-8

xn=2026
xq_m=0
xh=<student_id>
```

返回包含已选学分、已选门数和费用信息。HAR 中选课成功后从 `18.0` 学分、`7.0` 门变为 `20.0` 学分、`8.0` 门；退选后恢复。

## 课程列表接口

### 本年级/专业课程列表

```http
POST /taglib/DataTable.jsp?tableId=2568&fre=1
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
```

核心表单字段：

| 字段 | 示例 | 说明 |
| --- | --- | --- |
| `xktype` | `2` | 选课类型 |
| `xn` / `xq` | `2026` / `0` | 学年、学期 |
| `nj` | `2025` | 年级 |
| `zydm` | `0165` | 专业代码 |
| `_kcfw` / `kcfw` | `zxbnj` | 课程范围 |
| `lcid` | `<round_id>` | 轮次 ID |
| `njzy` | `2025|网络工程` | 年级专业 |
| `kcmc` | 空或课程名 | 课程名过滤 |
| `menucode_current` | `S2020202` | 当前菜单 |

常见范围差异：

| 范围 | 额外字段 |
| --- | --- |
| `zxbnj` | `njzy=2025|网络工程` |
| `zxggrx` | 可带 `lbgl`、`kcsx`、`kcmc` |
| `zxknj` | 先通过年级专业下拉选择可跨年级/专业 |

响应是 DataTable HTML/脚本片段，课程行里会带课程代码、课程名、学分、已选教学班、候选教学班入口等信息。

## 教学班详情接口

打开某门课的教学班弹窗前，页面会先检查课程是否可选：

```http
POST /jw/common/isSelectableSkbjdm.action
Content-Type: application/x-www-form-urlencoded; charset=UTF-8

xn=2026
xq_m=0
xh=<student_id>
kcdm=<course_id>
```

随后进入弹窗：

```text
GET /student/report/wsxk.zx_promt.jsp?params=<encrypted_params>&token=<token>&timestamp=<ts>
```

弹窗内部的教学班表：

```http
POST /taglib/DataTable.jsp?tableId=6142&fre=1&xn=2026&xq_m=0&xh=<student_id>&kcdm=<course_id>&skbjdm=&xktype=2&kcfw=<scope>&isyxkc=false&lcid=<round_id>
```

响应列通常包括：

| 列 | 说明 |
| --- | --- |
| 上课班号 | 教学班号，如 `04500142-010` |
| 上课班级名称 | 面向班级，如 `25网工4+网工5（1）` |
| 开课校区 | 校区 |
| 任课教师 | 教师姓名 |
| 限选人数 | 容量 |
| 已选/免听 | 当前人数 |
| 可选人数 | 剩余名额 |
| 上课时间 | 星期、节次、单双周 |
| 上课地点 | 教室 |
| 选择 | 前端选择按钮 |

这些数据适合用于本地排课规划。比如网络工程四班应优先关注教学班名称中包含 `25网工4` 的行，再按时间集中度、冲突、剩余名额排序。

## 提交与退选边界

真实选课提交不是稳定明文表单。前端会序列化弹窗内 `ActionForm`，去掉 `electiveCourseForm.` 前缀，再通过页面脚本生成加密 `params`：

```http
POST /jw/common/saveElectiveCourse.action
Content-Type: application/x-www-form-urlencoded; charset=UTF-8

params=<encrypted_params>
token=<token>
timestamp=<ts>
```

退选接口同样使用加密参数：

```http
POST /jw/common/cancelElectiveCourse.action
Content-Type: application/x-www-form-urlencoded; charset=UTF-8

params=<encrypted_params>
token=<token>
timestamp=<ts>
```

因此脚本中不要复用历史 HAR 的 `params`、`token` 或 `timestamp`。后续工具只应实现：

- 只读抓取选课状态、课程列表、教学班详情。
- 本地生成无冲突、课程集中的候选方案。
- 在用户确认后打开官方页面或弹窗定位目标教学班。
- 不做高频轮询、并发抢占、验证码绕过或加密参数伪造。

## 退选列表

```http
POST /taglib/DataTable.jsp?tableId=6093&fre=1
Content-Type: application/x-www-form-urlencoded; charset=UTF-8

xktype=5
xh=<student_id>
xn=2026
xq=0
nj=2025
zydm=0165
lcid=<round_id>
kcfw=All
menucode_current=S2020205
```

该列表用于展示已选课程和退选入口；实际退选仍走 `cancelElectiveCourse.action` 的加密参数流程。

## 规划建议

对“网络工程四班、课程集中在一起”的默认策略：

1. 用 `tableId=2568` 获取本年级/专业候选课程。
2. 对每门目标课程打开 `tableId=6142` 教学班详情。
3. 优先保留 `上课班级名称` 包含 `25网工4` 的教学班。
4. 过滤与已选课冲突的教学班。
5. 按更少上课天数、避免晚课、剩余名额更高排序。
6. 输出人工确认清单，不直接提交。
