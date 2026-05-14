"""
Utility functions: Excel export, desktop notifications, clipboard operations.
"""
from datetime import date, datetime
from pathlib import Path

import pandas as pd
from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox
from PyQt5.QtCore import QStandardPaths
from plyer import notification


def export_to_excel(session_factory) -> str | None:
    """Export all data tables to a single Excel file with multiple sheets.

    Returns the file path on success, None on failure.
    """
    desktop = QStandardPaths.writableLocation(QStandardPaths.DesktopLocation)
    default_name = f"baoyan_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    path, _ = QFileDialog.getSaveFileName(
        None, "导出数据为 Excel", str(Path(desktop) / default_name),
        "Excel Files (*.xlsx)"
    )
    if not path:
        return None

    from database import get_all_projects, get_all_interviews, get_all_mentors, get_all_templates

    with session_factory() as session:
        projects = get_all_projects(session)
        interviews = get_all_interviews(session)
        mentors = get_all_mentors(session)
        templates = get_all_templates(session)

        # Build project export
        pdata = []
        for p in projects:
            pdata.append({
                "ID": p.id, "院校": p.school, "学院": p.college, "专业": p.major,
                "学位类型": p.degree_type, "批次": p.batch, "状态": p.status,
                "标签": p.tags, "官网链接": p.official_link, "备注": p.notes,
                "创建时间": str(p.created_at)[:19] if p.created_at else "",
            })
            # Materials for this project
            mdata = []
            for m in p.materials:
                mdata.append({
                    "项目ID": p.id, "材料名称": m.name, "状态": m.status,
                    "文件路径": m.file_path,
                })
            # Timelines
            tldata = []
            for tl in p.timelines:
                tldata.append({
                    "项目ID": p.id, "节点名称": tl.name,
                    "日期": str(tl.date) if tl.date else "", "描述": tl.description,
                })
            # Interviews
            ivdata = []
            for iv in p.interviews:
                ivdata.append({
                    "项目ID": p.id,
                    "面试日期": str(iv.date) if iv.date else "",
                    "形式": iv.format_type, "问题": iv.questions,
                    "评分(1-5)": iv.self_rating, "总结": iv.summary, "笔记": iv.notes,
                })

        # Mentor data
        mtrdata = []
        for m in mentors:
            mtrdata.append({
                "ID": m.id, "导师姓名": m.name, "院校": m.school,
                "研究方向": m.research_direction, "邮箱": m.email,
                "首次联系日": str(m.first_contact_date) if m.first_contact_date else "",
                "状态": m.status, "回复摘要": m.reply_summary,
                "下次跟进": str(m.next_followup_date) if m.next_followup_date else "",
                "备注": m.notes,
            })

        # Template data
        tpldata = []
        for t in templates:
            tpldata.append({
                "ID": t.id, "标题": t.title, "分类": t.category,
                "内容": t.content,
            })

    # Write Excel
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        if pdata:
            pd.DataFrame(pdata).to_excel(writer, sheet_name="项目", index=False)
        if mdata:
            pd.DataFrame(mdata).to_excel(writer, sheet_name="材料", index=False)
        if tldata:
            pd.DataFrame(tldata).to_excel(writer, sheet_name="时间节点", index=False)
        if ivdata:
            pd.DataFrame(ivdata).to_excel(writer, sheet_name="面试记录", index=False)
        if mtrdata:
            pd.DataFrame(mtrdata).to_excel(writer, sheet_name="导师联系", index=False)
        if tpldata:
            pd.DataFrame(tpldata).to_excel(writer, sheet_name="文书模板", index=False)

    QMessageBox.information(None, "导出成功", f"数据已成功导出到:\n{path}")
    return path


def send_desktop_notification(title: str, message: str) -> None:
    """Send a system desktop notification using plyer."""
    try:
        notification.notify(
            title=title,
            message=message,
            app_name="保研全程管理",
            timeout=8,
        )
    except Exception:
        # plyer may not work on all platforms; degrade gracefully
        pass


def copy_to_clipboard(text: str) -> None:
    """Copy text to system clipboard."""
    clipboard = QApplication.clipboard()
    if clipboard:
        clipboard.setText(text)


def _export_data_silent(session_factory, path: str) -> bool:
    """Export data to a path without user interaction (for scheduled use)."""
    try:
        from database import get_all_projects, get_all_interviews, get_all_mentors, get_all_templates

        with session_factory() as session:
            projects = get_all_projects(session)
            interviews = get_all_interviews(session)
            mentors = get_all_mentors(session)
            templates = get_all_templates(session)

            pdata, mdata, tldata, ivdata = [], [], [], []
            for p in projects:
                pdata.append({
                    "ID": p.id, "院校": p.school, "学院": p.college, "专业": p.major,
                    "学位类型": p.degree_type, "批次": p.batch, "状态": p.status,
                    "标签": p.tags, "官网链接": p.official_link,
                })
                for m in p.materials:
                    mdata.append({"项目ID": p.id, "材料名称": m.name, "状态": m.status, "文件路径": m.file_path})
                for tl in p.timelines:
                    tldata.append({"项目ID": p.id, "节点名称": tl.name, "日期": str(tl.date) if tl.date else "", "描述": tl.description})
                for iv in p.interviews:
                    ivdata.append({
                        "项目ID": p.id, "面试日期": str(iv.date) if iv.date else "",
                        "形式": iv.format_type, "评分(1-5)": iv.self_rating, "总结": iv.summary,
                    })

            mtrdata = [{"ID": m.id, "导师姓名": m.name, "院校": m.school, "研究方向": m.research_direction,
                        "邮箱": m.email, "状态": m.status, "下次跟进": str(m.next_followup_date) if m.next_followup_date else ""}
                       for m in mentors]
            tpldata = [{"ID": t.id, "标题": t.title, "分类": t.category, "内容": t.content} for t in templates]

        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            if pdata: pd.DataFrame(pdata).to_excel(writer, sheet_name="项目", index=False)
            if mdata: pd.DataFrame(mdata).to_excel(writer, sheet_name="材料", index=False)
            if tldata: pd.DataFrame(tldata).to_excel(writer, sheet_name="时间节点", index=False)
            if ivdata: pd.DataFrame(ivdata).to_excel(writer, sheet_name="面试记录", index=False)
            if mtrdata: pd.DataFrame(mtrdata).to_excel(writer, sheet_name="导师联系", index=False)
            if tpldata: pd.DataFrame(tpldata).to_excel(writer, sheet_name="文书模板", index=False)
        return True
    except Exception:
        return False
