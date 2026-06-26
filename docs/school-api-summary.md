# 河南大学校园相关 API 汇总（主分支 Docs）

本文档用于把仓库内出现的“校园相关 API 接口”集中到一个地方，方便对接与维护。  
仓库为多变体并行结构（`mcp-server` / `agent-skill` / `langbot-plugin`），但下述网络接口在三套代码中基本共享同一套上游实现。

> 说明：本文件按服务域名分组；每个区域都对应仓库里的真实调用点，建议对接时以该文件为入口清单再回溯到对应实现文件。

## 一、统一认证链路

CAS 登录入口（多系统共用）:

- `https://ids.henu.edu.cn/authserver/login`
- `https://ids.henu.edu.cn/authserver/login?service=https://xk.henu.edu.cn/caslogin`
- `https://ids.henu.edu.cn/authserver/login?service=https://zwyy.henu.edu.cn/v4/login/cas`
- `https://ids.henu.edu.cn/authserver/login?service=https://yzsfz.henu.edu.cn/fapi/v4/login/cas`

## 二、选课系统（xk.henu.edu.cn）相关接口

主要来自 `course-selection-api.md` 与 `course_selection.py`。

1. 入口与主界面
- `GET /frame/homes.action?v=...`
- `GET /frame/jw/teacherstudentmenu.jsp?menucode=S20202`
- `GET /student/wsxk.zx.html?menucode=S2020202&bqflag=1`

2. 选课状态 / 下拉 / 课程列表
- `POST /jw/common/getWsxkTimeRange.action?xktype=2`
- `POST /frame/droplist/getDropLists.action`
- `POST /taglib/DataTable.jsp?tableId=2568&fre=1`
- `POST /taglib/DataTable.jsp?tableId=6142&fre=1...`（教学班详情）

3. 课程确认页与提交（高风险/需人工边界）
- `GET /student/report/wsxk.zx_promt.jsp?...`（弹窗页）
- `POST /jw/common/isSelectableSkbjdm.action`
- `POST /jw/common/saveElectiveCourse.action`
- `POST /jw/common/cancelElectiveCourse.action`

4. 课表相关抓取
- `GET /frame/home/js/SetMainInfo.jsp`
- `GET /student/xkjg.wdkb.jsp`
- `GET /wsxk/xkjg.ckdgxsxdkchj_data.jsp` / `..._10319.jsp`
- `GET /student/wsxk.xskcb.jsp` / `...xskcb10319.jsp`

## 三、课程表抓取与空教室模块（xk.henu.edu.cn）

主要来自 `henu_empty_classroom_api_doc.md` 与 `course_schedule.py`：

1. 上游公共查询
- `POST /frame/droplist/getDropLists.action`（复用）
- `POST /taglib/CombBoxServlet.jsp`
- `POST /kbbp/dykb.GS1.jsp?kblx=jsikb`
- `POST /kbbp/dykb.GS1_exp.jsp?kblx=jsikb`（导出）

2. 空教室模块项目化接口（见下文“项目侧统一接口”）

## 四、图书馆与研讨室（zwyy.henu.edu.cn）相关接口

主要来源：`campus_core/auth.py`, `campus_core/locations.py`, `campus_core/seat_reservation.py`,
`campus_core/seminar.py`，文件在 `mcp-server/campus_core/` 下。

- 认证与会话
- `POST /v4/login/cas`
- `POST /v4/login/user`（CAS ticket 置换）

- 通用图书馆能力
- `POST /v4/space/pick`
- `POST /v4/Space/map`
- `POST /v4/member/checkStudyOpenTime`
- `POST /v4/Space/seat`
- `POST /v4/index/subscribe`
- `POST /v4/member/seat`
- `POST /v4/space/confirm`（普通座位预约）
- `POST /v4/space/studyConfirm`（学习类预约）
- `POST /v4/space/signin`
- `POST /v4/space/studySign`
- `POST /v4/space/cancel`
- `POST /v4/space/studyCancel`

- 研讨室能力
- `POST /v4/seminar/siftdate`
- `POST /v4/seminar/sift`
- `POST /v4/seminar/list`
- `POST /v4/seminar/detail`
- `POST /v4/seminar/seminar`
- `POST /v4/seminar/members`
- `POST /v4/seminar/confirm`
- `POST /v4/seminar/submit`
- `POST /v4/seminar/books`
- `POST /v4/seminar/reneges`
- `POST /v4/seminar/cancel`
- `POST /v4/seminar/signin`

## 五、河宝社区（yzsfz.henu.edu.cn）相关接口

主要来源：`campus_core/hebao.py`

- `GET /activity-registration/registrationProgress/h5Task`
- `GET /studentleave/studentLeaveInfo/approveLeaveInfo`
- `GET /studentleave/studentLeaveInfo/{leave_id}`
- `POST /studentleave/studentLeaveInfo/submit`
- `POST /studentleave/studentLeaveInfo/cancel/{leave_id}`
- `POST /studentleave/studentLeaveInfo/confirmReturn/{leave_id}`
- `GET /sign-in/stu-task/list`
- `POST /sign-in/student-task/signIn`
- `GET /check-sleep/stu-task/list`
- `POST /check-sleep/student-task/check`
- `GET /activity-registration/registrationProgress/page/my-activity`
- `POST /activity-registration/registration/register/{activity_id}`
- `GET /infocollection/questionnaire/studentQuestionnaireProgress`

## 六、项目侧统一接口（本仓库 `/api/v1`）

主要来自 `henu_empty_classroom_api_doc.md`：

- `GET /api/v1/terms`
- `GET /api/v1/campuses`
- `GET /api/v1/classroom-types`
- `GET /api/v1/buildings`
- `GET /api/v1/classrooms`
- `POST /api/v1/classroom-schedules/sync`
- `GET /api/v1/free-classrooms`
- `GET /api/v1/classroom-occupancy`
- `GET /api/v1/free-classrooms/day-matrix`

## 七、接口来源说明

- 文件层：
  - `repo/docs/course-selection-api.md`（课程入口与选课 API）
  - `repo/docs/henu_empty_classroom_api_doc.md`（空教室接口与课表逆向逻辑）
  - `mcp-server/course_selection.py`
  - `mcp-server/course_schedule.py`
  - `mcp-server/campus_core/auth.py`
  - `mcp-server/campus_core/locations.py`
  - `mcp-server/campus_core/seat_reservation.py`
  - `mcp-server/campus_core/seminar.py`
  - `mcp-server/campus_core/hebao.py`
- 变体一致性：
  - `agent-skill` 与 `langbot-plugin` 下均为同源实现（路径与接口语义一致），建议只在本汇总文件维护改动，避免三套同时维护造成漂移。
