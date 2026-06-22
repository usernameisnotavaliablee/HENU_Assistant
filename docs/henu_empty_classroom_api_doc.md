# 河南大学空教室查询 API 文档

版本：v1.0  
模块：空教室查询 / 教室课表解析  
上游系统：河南大学选课系统 `https://xk.henu.edu.cn`  
数据来源：教室课表页面 `公共查询 → 教室课表`

> 说明：上游系统返回的是“教室课表”，不是直接返回“空教室”。本模块需要先拉取教室课表 HTML，再根据目标周次、星期、节次反向计算空闲教室。本文档不包含任何 Cookie、Token、账号密码等敏感信息。

---

## 1. 基本约定

### 1.1 项目侧 Base URL

```http
/api/v1
```

### 1.2 上游 Base URL

```http
https://xk.henu.edu.cn
```

### 1.3 通用响应格式

```json
{
  "code": 0,
  "message": "ok",
  "data": {}
}
```

### 1.4 通用错误码

| code | 含义 | 说明 |
|---:|---|---|
| 0 | 成功 | 请求正常 |
| 40001 | 参数错误 | 缺少必要参数或参数格式错误 |
| 40101 | 登录态失效 | 上游选课系统 Session 失效，需要重新登录 |
| 40401 | 资源不存在 | 学期、校区、楼房或教室不存在 |
| 42901 | 请求过于频繁 | 触发限流 |
| 50001 | 解析失败 | 上游 HTML / XML 结构变化，解析失败 |
| 50201 | 上游接口异常 | 上游系统不可用或返回异常 |

### 1.5 时间编码规则

#### 星期编码

| dayOfWeek | 含义 |
|---:|---|
| 1 | 星期一 |
| 2 | 星期二 |
| 3 | 星期三 |
| 4 | 星期四 |
| 5 | 星期五 |
| 6 | 星期六 |
| 7 | 星期日 |

#### 课表大节编码

| period | 含义 | 常见实际节次 |
|---:|---|---|
| 1 | 第一大节 | 1-2 节 |
| 2 | 第二大节 | 3-4 / 3-5 节 |
| 9 | 中午时段 | 中午占用格，通常可忽略 |
| 3 | 第三大节 | 6-8 / 7-8 节 |
| 4 | 第四大节 | 9-10 节 |
| 5 | 第五大节 | 11-12 / 11-13 节 |

> 注意：上游课表格子使用“大节”布局，实际节次以格子内课程文本为准。空教室查询推荐使用 `period=1,2,3,4,5`。

---

## 2. 上游接口说明

以下接口由后端调用，不建议前端直接访问。后端需要维护用户登录态，并对 Cookie / Session 做安全隔离。

---

### 2.1 获取学期列表

**接口名称**：获取学期下拉列表  
**请求方式**：POST  
**接口地址**：

```http
/frame/droplist/getDropLists.action
```

**Content-Type**：

```http
application/x-www-form-urlencoded
```

**请求参数**：

| 参数名 | 类型 | 必填 | 示例 | 说明 |
|---|---|---:|---|---|
| comboBoxName | string | 是 | Ms_KBBP_FBXQLLJXAP | 学期下拉列表标识 |
| paramValue | string | 否 | 空字符串 | 附加参数 |
| isYXB | number | 否 | 0 | 固定参数 |
| isCDDW | number | 否 | 0 | 固定参数 |
| isXQ | number | 否 | 0 | 固定参数 |
| isDJKSLB | number | 否 | 0 | 固定参数 |
| isZY | number | 否 | 0 | 固定参数 |

**请求示例**：

```text
comboBoxName=Ms_KBBP_FBXQLLJXAP&paramValue=&isYXB=0&isCDDW=0&isXQ=0&isDJKSLB=0&isZY=0
```

**上游响应示例**：

```json
[
  {
    "code": "2025,1",
    "name": "2025-2026学年第二学期"
  },
  {
    "code": "2025,0",
    "name": "2025-2026学年第一学期"
  }
]
```

---

### 2.2 获取校区列表

**接口名称**：获取校区列表  
**请求方式**：POST  
**接口地址**：

```http
/frame/droplist/getDropLists.action
```

**请求参数**：

| 参数名 | 类型 | 必填 | 示例 | 说明 |
|---|---|---:|---|---|
| comboBoxName | string | 是 | MsSchoolArea | 校区下拉列表标识 |
| paramValue | string | 否 | 空字符串 | 附加参数 |
| isYXB | number | 否 | 0 | 固定参数 |
| isCDDW | number | 否 | 0 | 固定参数 |
| isXQ | number | 否 | 0 | 固定参数 |
| isDJKSLB | number | 否 | 0 | 固定参数 |
| isZY | number | 否 | 0 | 固定参数 |

**响应示例**：

```json
[
  { "code": "01", "name": "明伦校区" },
  { "code": "02", "name": "金明校区" },
  { "code": "03", "name": "郑州校区" },
  { "code": "04", "name": "其他校区" }
]
```

---

### 2.3 获取教室类型列表

**接口名称**：获取教室类型  
**请求方式**：POST  
**接口地址**：

```http
/frame/droplist/getDropLists.action
```

**请求参数**：

| 参数名 | 类型 | 必填 | 示例 | 说明 |
|---|---|---:|---|---|
| comboBoxName | string | 是 | MsCodeset | 代码集下拉列表标识 |
| paramValue | string | 是 | DM-JSLX | 教室类型代码集 |
| isYXB | number | 否 | 0 | 固定参数 |
| isCDDW | number | 否 | 0 | 固定参数 |
| isXQ | number | 否 | 0 | 固定参数 |
| isDJKSLB | number | 否 | 0 | 固定参数 |
| isZY | number | 否 | 0 | 固定参数 |

**响应示例**：

```json
[
  { "code": "00", "name": "不安排教室" },
  { "code": "01", "name": "一般教室" },
  { "code": "05", "name": "多媒体教室" },
  { "code": "06", "name": "师范生实训中心教室" }
]
```

---

### 2.4 获取楼房列表

**接口名称**：按校区获取楼房列表  
**请求方式**：POST  
**接口地址**：

```http
/frame/droplist/getDropLists.action
```

**请求参数**：

| 参数名 | 类型 | 必填 | 示例 | 说明 |
|---|---|---:|---|---|
| comboBoxName | string | 是 | MsSchoolArea_LF | 校区楼房下拉列表标识 |
| paramValue | string | 是 | ssxq=01 | 所属校区，需 URL 编码 |
| isYXB | number | 否 | 0 | 固定参数 |
| isCDDW | number | 否 | 0 | 固定参数 |
| isXQ | number | 否 | 0 | 固定参数 |
| isDJKSLB | number | 否 | 0 | 固定参数 |
| isZY | number | 否 | 0 | 固定参数 |

**请求示例**：

```text
comboBoxName=MsSchoolArea_LF&paramValue=ssxq%3D01&isYXB=0&isCDDW=0&isXQ=0&isDJKSLB=0&isZY=0
```

**响应示例**：

```json
[
  { "code": "0013", "name": "十号楼" },
  { "code": "0003", "name": "综合教学楼" }
]
```

---

### 2.5 获取教室列表

**接口名称**：按校区 / 楼房 / 类型获取教室列表  
**请求方式**：POST  
**接口地址**：

```http
/taglib/CombBoxServlet.jsp
```

**Content-Type**：

```http
application/x-www-form-urlencoded
```

**请求参数**：

| 参数名 | 类型 | 必填 | 示例 | 说明 |
|---|---|---:|---|---|
| className | string | 是 | jxap_combbox_js | 固定值，表示教室下拉数据 |
| loadDataStyle | string | 是 | loadClass | 固定值 |
| xq_m | string | 否 | 01 | 校区代码，空表示全部校区 |
| jslx_m | string | 否 | 05 | 教室类型代码，空表示全部类型 |
| lf_m | string | 否 | 0013 | 楼房代码，空表示全部楼房 |
| flag | string | 是 | xkyjs | 固定值 |

**请求示例**：

```text
className=jxap_combbox_js&loadDataStyle=loadClass&xq_m=01&jslx_m=&lf_m=0013&flag=xkyjs&
```

**上游响应格式**：XML

**上游响应示例**：

```xml
<data>
  <info>
    <filtrateCount>1</filtrateCount>
    <value>0000231</value>
    <filtrateInfo0>十号楼101</filtrateInfo0>
    <name>十号楼101[160][多媒体教室]</name>
    <fillName>十号楼101[160][多媒体教室]</fillName>
  </info>
</data>
```

**解析规则**：

| 字段 | 来源 | 示例 |
|---|---|---|
| roomId | value | 0000231 |
| roomName | filtrateInfo0 | 十号楼101 |
| capacity | name 中第一个方括号 | 160 |
| roomType | name 中第二个方括号 | 多媒体教室 |

---

### 2.6 获取教室课表 HTML

**接口名称**：获取教室课表  
**请求方式**：POST  
**接口地址**：

```http
/kbbp/dykb.GS1.jsp?kblx=jsikb
```

**Content-Type**：

```http
application/x-www-form-urlencoded
```

**核心请求参数**：

| 参数名 | 类型 | 必填 | 示例 | 说明 |
|---|---|---:|---|---|
| xnxq | string | 是 | 2025,1 | 学期代码 |
| xn | string | 是 | 2025 | 学年开始年份，通常取 xnxq 逗号前部分 |
| xq_m | string | 是 | 1 | 学期标识，通常取 xnxq 逗号后部分 |
| selXQ | string | 是 | 01 | 校区代码 |
| selLF | string | 否 | 0013 | 楼房代码 |
| jslx | string | 否 | 05 | 教室类型代码 |
| hidXQ | string | 是 | 01 | 隐藏字段，校区代码 |
| hidLF | string | 否 | 0013 | 隐藏字段，楼房代码 |
| hidJSLX | string | 否 | 05 | 隐藏字段，教室类型代码 |
| hidCXLX | string | 是 | flf | 查询类型，flf 表示按楼房查询 |
| userType | string | 是 | STU | 用户类型 |
| xkyjs | string | 是 | 1 | 查看空余教室相关开关 |
| selGS | string | 是 | 1 | 显示格式 |
| menucode_current | string | 是 | SB04 | 菜单代码 |

**推荐完整请求体模板**：

```text
hidFJBH=&hidXQ={campusCode}&hidLF={buildingCode}&userType=STU&hidJSLX={roomTypeCode}&hidSYDW=&hidCXLX=flf&hidBfy=0&hidZZLX=A4&orientation=L&xssj=xssj&xsrq=xsrq&sfxsym=xsym&lx=&xkyjs=1&xnxq={termCode}&xn={year}&xn1=&_xq=&xq_m={termPart}&jslx={roomTypeCode}&selGS=1&selXQ={campusCode}&selLF={buildingCode}&txt_jsmc=&skdd=&selSYDW=&selJSMC=&radioa=on&chkXSDYRQ=on&chkXSDYSJ=on&chkXSYM=on&chkXKYJS=on&radiob=A4&radiofx=hx&chk_week6=1&chk_week7=1&menucode_current=SB04
```

**请求示例**：

```text
hidFJBH=&hidXQ=01&hidLF=0013&userType=STU&hidJSLX=&hidSYDW=&hidCXLX=flf&hidBfy=0&hidZZLX=A4&orientation=L&xssj=xssj&xsrq=xsrq&sfxsym=xsym&lx=&xkyjs=1&xnxq=2025%2C1&xn=2025&xn1=&_xq=&xq_m=1&jslx=&selGS=1&selXQ=01&selLF=0013&txt_jsmc=&skdd=&selSYDW=&selJSMC=&radioa=on&chkXSDYRQ=on&chkXSDYSJ=on&chkXSYM=on&chkXKYJS=on&radiob=A4&radiofx=hx&chk_week6=1&chk_week7=1&menucode_current=SB04
```

**上游响应格式**：HTML

**解析说明**：

1. 每个教室对应一个课表 `table`，例如 `mytable0`、`mytable1`。
2. 教室名称、容量在 table 前方的描述区中，例如 `教室：十号楼101(160)`。
3. 每个课程格子位于 `div.div1` 中。
4. `div` 的 `id` 可以按 `tableIndex + dayOfWeek + period` 理解：
   - `011`：第 0 个教室表，星期一，第一大节。
   - `021`：第 0 个教室表，星期二，第一大节。
   - `1011`：第 10 个教室表，星期一，第一大节。
5. `div` 文本为空，表示该格没有课程。
6. `div` 文本不为空时，需要继续解析周次，例如 `[1-18]周`、`[1-5,7-18]周`、`单周`、`双周`。

---

### 2.7 导出教室课表 Excel

**接口名称**：导出教室课表  
**请求方式**：POST  
**接口地址**：

```http
/kbbp/dykb.GS1_exp.jsp?kblx=jsikb
```

**说明**：该接口返回 `application/vnd.ms-excel`，实际内容仍然接近 HTML 表格。可用于人工导出，不建议作为空教室查询的主解析入口。

---

## 3. 项目侧业务 API

项目侧 API 面向前端、小程序或其他服务。前端只调用项目后端，不直接调用上游选课系统。

---

### 3.1 查询学期列表

**接口名称**：查询学期列表  
**请求方式**：GET  
**接口地址**：

```http
/api/v1/terms
```

**请求参数**：无

**响应示例**：

```json
{
  "code": 0,
  "message": "ok",
  "data": [
    {
      "termCode": "2025,1",
      "termName": "2025-2026学年第二学期",
      "year": "2025",
      "termPart": "1"
    }
  ]
}
```

---

### 3.2 查询校区列表

**接口名称**：查询校区列表  
**请求方式**：GET  
**接口地址**：

```http
/api/v1/campuses
```

**响应示例**：

```json
{
  "code": 0,
  "message": "ok",
  "data": [
    { "campusCode": "01", "campusName": "明伦校区" },
    { "campusCode": "02", "campusName": "金明校区" },
    { "campusCode": "03", "campusName": "郑州校区" },
    { "campusCode": "04", "campusName": "其他校区" }
  ]
}
```

---

### 3.3 查询教室类型列表

**接口名称**：查询教室类型列表  
**请求方式**：GET  
**接口地址**：

```http
/api/v1/classroom-types
```

**响应示例**：

```json
{
  "code": 0,
  "message": "ok",
  "data": [
    { "typeCode": "01", "typeName": "一般教室" },
    { "typeCode": "05", "typeName": "多媒体教室" },
    { "typeCode": "06", "typeName": "师范生实训中心教室" }
  ]
}
```

---

### 3.4 查询楼房列表

**接口名称**：按校区查询楼房列表  
**请求方式**：GET  
**接口地址**：

```http
/api/v1/buildings
```

**请求参数**：

| 参数名 | 类型 | 必填 | 示例 | 说明 |
|---|---|---:|---|---|
| campusCode | string | 是 | 01 | 校区代码 |

**请求示例**：

```http
GET /api/v1/buildings?campusCode=01
```

**响应示例**：

```json
{
  "code": 0,
  "message": "ok",
  "data": [
    { "buildingCode": "0013", "buildingName": "十号楼", "campusCode": "01" },
    { "buildingCode": "0003", "buildingName": "综合教学楼", "campusCode": "01" }
  ]
}
```

---

### 3.5 查询教室列表

**接口名称**：查询教室列表  
**请求方式**：GET  
**接口地址**：

```http
/api/v1/classrooms
```

**请求参数**：

| 参数名 | 类型 | 必填 | 示例 | 说明 |
|---|---|---:|---|---|
| campusCode | string | 否 | 01 | 校区代码 |
| buildingCode | string | 否 | 0013 | 楼房代码 |
| typeCode | string | 否 | 05 | 教室类型代码 |
| keyword | string | 否 | 十号楼101 | 教室名称关键词 |

**请求示例**：

```http
GET /api/v1/classrooms?campusCode=01&buildingCode=0013&typeCode=05
```

**响应示例**：

```json
{
  "code": 0,
  "message": "ok",
  "data": [
    {
      "roomId": "0000231",
      "roomName": "十号楼101",
      "campusCode": "01",
      "campusName": "明伦校区",
      "buildingCode": "0013",
      "buildingName": "十号楼",
      "capacity": 160,
      "typeName": "多媒体教室"
    },
    {
      "roomId": "0000232",
      "roomName": "十号楼102",
      "campusCode": "01",
      "campusName": "明伦校区",
      "buildingCode": "0013",
      "buildingName": "十号楼",
      "capacity": 140,
      "typeName": "多媒体教室"
    }
  ]
}
```

---

### 3.6 同步教室课表

**接口名称**：同步指定楼房教室课表  
**请求方式**：POST  
**接口地址**：

```http
/api/v1/classroom-schedules/sync
```

**说明**：后端调用上游 `dykb.GS1.jsp?kblx=jsikb`，获取指定学期、校区、楼房的教室课表 HTML，解析后写入本地缓存或数据库。

**请求体**：

```json
{
  "termCode": "2025,1",
  "campusCode": "01",
  "buildingCode": "0013",
  "typeCode": "",
  "forceRefresh": false
}
```

**请求参数说明**：

| 参数名 | 类型 | 必填 | 示例 | 说明 |
|---|---|---:|---|---|
| termCode | string | 是 | 2025,1 | 学期代码 |
| campusCode | string | 是 | 01 | 校区代码 |
| buildingCode | string | 是 | 0013 | 楼房代码 |
| typeCode | string | 否 | 05 | 教室类型，空表示全部类型 |
| forceRefresh | boolean | 否 | false | 是否强制刷新上游数据 |

**响应示例**：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "termCode": "2025,1",
    "campusCode": "01",
    "buildingCode": "0013",
    "syncStatus": "success",
    "roomCount": 18,
    "scheduleCellCount": 756,
    "updatedAt": "2026-06-22 10:30:00"
  }
}
```

---

### 3.7 查询空教室

**接口名称**：查询空教室  
**请求方式**：GET  
**接口地址**：

```http
/api/v1/free-classrooms
```

**请求参数**：

| 参数名 | 类型 | 必填 | 示例 | 说明 |
|---|---|---:|---|---|
| termCode | string | 是 | 2025,1 | 学期代码 |
| week | number | 是 | 18 | 教学周 |
| dayOfWeek | number | 是 | 1 | 星期，1-7 |
| period | number | 是 | 2 | 大节，1/2/3/4/5，9 表示中午 |
| campusCode | string | 否 | 01 | 校区代码 |
| buildingCode | string | 否 | 0013 | 楼房代码 |
| typeCode | string | 否 | 05 | 教室类型代码 |
| minCapacity | number | 否 | 60 | 最小容量 |
| keyword | string | 否 | 十号楼 | 教室名称关键词 |
| useCache | boolean | 否 | true | 是否优先使用缓存 |

**请求示例**：

```http
GET /api/v1/free-classrooms?termCode=2025,1&week=18&dayOfWeek=1&period=2&campusCode=01&buildingCode=0013&minCapacity=60
```

**响应示例**：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "query": {
      "termCode": "2025,1",
      "termName": "2025-2026学年第二学期",
      "week": 18,
      "dayOfWeek": 1,
      "dayName": "星期一",
      "period": 2,
      "periodName": "第二大节",
      "campusCode": "01",
      "campusName": "明伦校区",
      "buildingCode": "0013",
      "buildingName": "十号楼",
      "minCapacity": 60
    },
    "total": 2,
    "rooms": [
      {
        "roomId": "0000232",
        "roomName": "十号楼102",
        "campusCode": "01",
        "campusName": "明伦校区",
        "buildingCode": "0013",
        "buildingName": "十号楼",
        "capacity": 140,
        "typeName": "多媒体教室",
        "status": "free"
      },
      {
        "roomId": "0000233",
        "roomName": "十号楼103",
        "campusCode": "01",
        "campusName": "明伦校区",
        "buildingCode": "0013",
        "buildingName": "十号楼",
        "capacity": 140,
        "typeName": "多媒体教室",
        "status": "free"
      }
    ],
    "cache": {
      "hit": true,
      "updatedAt": "2026-06-22 10:30:00"
    }
  }
}
```

---

### 3.8 查询教室占用详情

**接口名称**：查询单个教室某时间段占用情况  
**请求方式**：GET  
**接口地址**：

```http
/api/v1/classroom-occupancy
```

**请求参数**：

| 参数名 | 类型 | 必填 | 示例 | 说明 |
|---|---|---:|---|---|
| termCode | string | 是 | 2025,1 | 学期代码 |
| roomId | string | 是 | 0000231 | 教室 ID |
| week | number | 是 | 18 | 教学周 |
| dayOfWeek | number | 是 | 1 | 星期 |
| period | number | 是 | 2 | 大节 |

**请求示例**：

```http
GET /api/v1/classroom-occupancy?termCode=2025,1&roomId=0000231&week=18&dayOfWeek=1&period=2
```

**响应示例：空闲**

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "roomId": "0000231",
    "roomName": "十号楼101",
    "week": 18,
    "dayOfWeek": 1,
    "period": 2,
    "status": "free",
    "courses": []
  }
}
```

**响应示例：占用**

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "roomId": "0000231",
    "roomName": "十号楼101",
    "week": 18,
    "dayOfWeek": 1,
    "period": 1,
    "status": "occupied",
    "courses": [
      {
        "courseName": "高等数学A（二）",
        "teacherName": "李鸿军",
        "weekText": "[1-18]周",
        "weeks": [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18],
        "sectionText": "1-2节",
        "className": "25软件选课6班",
        "studentCount": 94,
        "departmentName": "软件学院",
        "rawText": "高等数学A（二） 李鸿军 [1-18]周 1-2节 007 25软件选课6班 94 软件学院"
      }
    ]
  }
}
```

---

### 3.9 查询一天空教室矩阵

**接口名称**：查询某天空教室矩阵  
**请求方式**：GET  
**接口地址**：

```http
/api/v1/free-classrooms/day-matrix
```

**请求参数**：

| 参数名 | 类型 | 必填 | 示例 | 说明 |
|---|---|---:|---|---|
| termCode | string | 是 | 2025,1 | 学期代码 |
| week | number | 是 | 18 | 教学周 |
| dayOfWeek | number | 是 | 1 | 星期 |
| campusCode | string | 否 | 01 | 校区代码 |
| buildingCode | string | 否 | 0013 | 楼房代码 |
| minCapacity | number | 否 | 60 | 最小容量 |

**响应示例**：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "termCode": "2025,1",
    "week": 18,
    "dayOfWeek": 1,
    "periods": [
      {
        "period": 1,
        "periodName": "第一大节",
        "total": 6,
        "rooms": [
          { "roomId": "0000232", "roomName": "十号楼102", "capacity": 140 }
        ]
      },
      {
        "period": 2,
        "periodName": "第二大节",
        "total": 8,
        "rooms": [
          { "roomId": "0000231", "roomName": "十号楼101", "capacity": 160 }
        ]
      }
    ]
  }
}
```

---

## 4. 数据库设计建议

### 4.1 classroom_terms

| 字段 | 类型 | 说明 |
|---|---|---|
| id | bigint | 主键 |
| term_code | varchar(20) | 学期代码，如 `2025,1` |
| term_name | varchar(100) | 学期名称 |
| year | varchar(10) | 学年开始年份 |
| term_part | varchar(10) | 学期标识 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

### 4.2 classroom_buildings

| 字段 | 类型 | 说明 |
|---|---|---|
| id | bigint | 主键 |
| campus_code | varchar(20) | 校区代码 |
| campus_name | varchar(100) | 校区名称 |
| building_code | varchar(20) | 楼房代码 |
| building_name | varchar(100) | 楼房名称 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

### 4.3 classrooms

| 字段 | 类型 | 说明 |
|---|---|---|
| id | bigint | 主键 |
| room_id | varchar(50) | 上游教室 ID |
| room_name | varchar(100) | 教室名称 |
| campus_code | varchar(20) | 校区代码 |
| campus_name | varchar(100) | 校区名称 |
| building_code | varchar(20) | 楼房代码 |
| building_name | varchar(100) | 楼房名称 |
| capacity | int | 容量 |
| type_name | varchar(100) | 教室类型 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

### 4.4 classroom_schedule_cells

| 字段 | 类型 | 说明 |
|---|---|---|
| id | bigint | 主键 |
| term_code | varchar(20) | 学期代码 |
| room_id | varchar(50) | 教室 ID |
| room_name | varchar(100) | 教室名称 |
| week_expr | varchar(100) | 原始周次表达式，如 `[1-18]周` |
| week_bitmap | varchar(100) | 解析后的周次位图或逗号列表 |
| day_of_week | int | 星期，1-7 |
| period | int | 大节 |
| section_text | varchar(50) | 实际节次文本，如 `1-2节` |
| course_name | varchar(200) | 课程名称 |
| teacher_name | varchar(100) | 教师姓名 |
| class_name | varchar(200) | 班级名称 |
| student_count | int | 学生人数 |
| department_name | varchar(200) | 开课单位 |
| raw_text | text | 上游原始文本 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

---

## 5. 空教室判定规则

### 5.1 单格判定

某教室在指定 `termCode + week + dayOfWeek + period` 下满足以下条件，则认为空闲：

1. 该教室存在；
2. 指定时间格没有课程文本；或
3. 指定时间格有课程文本，但课程周次不包含目标 `week`。

### 5.2 周次解析规则

| 表达式 | 解析结果 |
|---|---|
| `[1-18]周` | 1 到 18 周 |
| `[1-5,7-18]周` | 1 到 5 周，7 到 18 周 |
| `[4]周` | 第 4 周 |
| `[1-18]周 单周` | 1 到 18 周中的单周 |
| `[1-18]周 双周` | 1 到 18 周中的双周 |

### 5.3 查询算法

```text
输入：termCode, week, dayOfWeek, period, campusCode, buildingCode

1. 查询本地是否已有该学期、校区、楼房的课表缓存。
2. 若没有缓存或 forceRefresh=true，则调用上游课表接口拉取 HTML。
3. 解析 HTML，得到所有教室、所有时间格、所有课程占用信息。
4. 找出目标范围内所有教室。
5. 排除在 week + dayOfWeek + period 下有课程占用的教室。
6. 返回剩余教室，即空教室列表。
```

---

## 6. 缓存与限流建议

1. 按 `termCode + campusCode + buildingCode + typeCode` 缓存课表。
2. 默认缓存时间建议为 12 小时或 24 小时。
3. 用户查询空教室时优先查本地缓存，不要每次都请求上游。
4. 后端同步接口增加限流，例如同一楼房 5 分钟内最多强制刷新 1 次。
5. 不在前端暴露上游 Cookie、JSESSIONID、route 等字段。
6. 不提交 HAR 文件、Cookie、登录态到 GitHub。

---

## 7. 推荐前端调用流程

```text
1. GET /api/v1/terms
2. GET /api/v1/campuses
3. GET /api/v1/buildings?campusCode=01
4. GET /api/v1/free-classrooms?termCode=2025,1&week=18&dayOfWeek=1&period=2&campusCode=01&buildingCode=0013
```

若后端无缓存：

```text
1. POST /api/v1/classroom-schedules/sync
2. GET /api/v1/free-classrooms
```

---

## 8. 后端实现注意事项

1. 上游返回 HTML 编码声明为 GBK，解析时注意字符编码。
2. 上游教室列表返回 XML，需要解析 `value`、`filtrateInfo0`、`name`。
3. 上游课表中同一格可能包含多门课，需要按 `<br>` 或文本行拆分。
4. 课程文本格式不是强类型 JSON，不要只靠固定下标，建议使用正则 + 容错解析。
5. 解析失败时保留 `rawText`，方便后续修正规则。
6. 生产环境中应对上游请求做重试、超时和熔断。
