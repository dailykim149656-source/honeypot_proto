from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import List, Optional
from weasyprint import HTML
from datetime import datetime
import io

router = APIRouter()


# Pydantic 모델 정의 (프론트엔드 HandoverData와 동일)
class Transferor(BaseModel):
    name: str
    position: str
    contact: str


class Transferee(BaseModel):
    name: str
    position: str
    contact: Optional[str] = ""
    startDate: Optional[str] = ""


class Overview(BaseModel):
    transferor: Transferor
    transferee: Transferee
    reason: Optional[str] = ""
    background: Optional[str] = ""
    period: Optional[str] = ""


class JobStatus(BaseModel):
    title: str
    responsibilities: List[str]
    authority: Optional[str] = ""
    reportingLine: Optional[str] = ""
    teamMission: Optional[str] = ""
    teamGoals: Optional[List[str]] = []


class Priority(BaseModel):
    title: str
    status: str
    deadline: str


class OngoingProject(BaseModel):
    name: str
    owner: str
    status: str
    progress: int
    deadline: str
    description: str


class Stakeholder(BaseModel):
    name: str
    role: str


class TeamMember(BaseModel):
    name: str
    position: str
    role: str
    notes: Optional[str] = ""


class Stakeholders(BaseModel):
    manager: Optional[str] = ""
    internal: List[Stakeholder] = []
    external: List[Stakeholder] = []


class Risks(BaseModel):
    issues: str
    risks: str


class Document(BaseModel):
    category: str
    name: str
    location: str


class System(BaseModel):
    name: str
    usage: str
    contact: str


class Resources(BaseModel):
    docs: List[Document] = []
    systems: List[System] = []


class Checklist(BaseModel):
    text: str
    completed: bool


class HandoverData(BaseModel):
    overview: Overview
    jobStatus: JobStatus
    priorities: List[Priority]
    stakeholders: Stakeholders
    teamMembers: List[TeamMember]
    ongoingProjects: List[OngoingProject]
    risks: Risks
    resources: Resources
    checklist: List[Checklist] = []


def generate_pdf_html(data: HandoverData) -> str:
    """HandoverData를 기반으로 PDF용 HTML 생성"""

    # 주요 책임 리스트 생성
    responsibilities_html = "\n".join([
        f"<li>{resp}</li>" for resp in data.jobStatus.responsibilities
    ])

    # 우선순위 과제 테이블 생성
    priorities_rows = "\n".join([
        f"""<tr>
            <td style="border: 1px solid black; padding: 8px; text-align: center;">{i+1}</td>
            <td style="border: 1px solid black; padding: 8px; font-weight: bold;">{p.title}</td>
            <td style="border: 1px solid black; padding: 8px; text-align: center;">{p.status}</td>
            <td style="border: 1px solid black; padding: 8px; text-align: center;">{p.deadline}</td>
        </tr>"""
        for i, p in enumerate(data.priorities)
    ])

    # 진행 중인 프로젝트 테이블 생성
    projects_rows = "\n".join([
        f"""<tr>
            <td style="border: 1px solid black; padding: 8px; font-weight: bold;">{p.name}</td>
            <td style="border: 1px solid black; padding: 8px; text-align: center;">{p.owner}</td>
            <td style="border: 1px solid black; padding: 8px; text-align: center;">{p.progress}%</td>
            <td style="border: 1px solid black; padding: 8px; font-size: 11px;">{p.description}</td>
        </tr>"""
        for p in data.ongoingProjects
    ]) if data.ongoingProjects else """
        <tr>
            <td colspan="4" style="border: 1px solid black; padding: 16px; text-align: center; color: #999;">
                진행 중인 프로젝트가 없습니다.
            </td>
        </tr>
    """

    # 참고 문서 리스트 생성
    docs_html = "\n".join([
        f"""<li>
            <span style="font-weight: bold;">[{doc.category}]</span> {doc.name}<br/>
            <span style="font-size: 11px; color: #666;">({doc.location})</span>
        </li>"""
        for doc in data.resources.docs
    ]) if data.resources.docs else "<li>없음</li>"

    current_date = datetime.now().strftime("%Y년 %m월 %d일")

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{
                size: A4;
                margin: 20mm;
            }}
            body {{
                font-family: 'Malgun Gothic', '맑은 고딕', sans-serif;
                line-height: 1.6;
                color: #000;
                background: white;
            }}
            h1 {{
                text-align: center;
                font-size: 28px;
                font-weight: bold;
                letter-spacing: 8px;
                margin-bottom: 8px;
                border-bottom: 2px solid black;
                padding-bottom: 16px;
            }}
            h2 {{
                font-size: 18px;
                font-weight: bold;
                margin-top: 32px;
                margin-bottom: 8px;
                border-left: 4px solid black;
                padding-left: 8px;
                text-transform: uppercase;
            }}
            .header-date {{
                text-align: center;
                font-size: 12px;
                color: #666;
                margin-bottom: 32px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 32px;
                font-size: 13px;
            }}
            th {{
                background-color: #f0f0f0;
                border: 1px solid black;
                padding: 8px;
                text-align: center;
                font-weight: bold;
            }}
            td {{
                border: 1px solid black;
                padding: 8px;
            }}
            .two-column {{
                display: flex;
                gap: 32px;
                margin-bottom: 32px;
            }}
            .two-column > div {{
                flex: 1;
            }}
            .border-box {{
                border: 1px solid black;
                padding: 16px;
                min-height: 100px;
                font-size: 13px;
            }}
            ul {{
                margin: 0;
                padding-left: 24px;
            }}
            li {{
                margin-bottom: 4px;
            }}
            .signature-section {{
                margin-top: 48px;
                padding-top: 32px;
                border-top: 2px solid #ccc;
                page-break-inside: avoid;
            }}
            .signature-text {{
                text-align: center;
                font-size: 13px;
                margin-bottom: 48px;
            }}
            .signatures {{
                display: flex;
                justify-content: space-around;
                text-align: center;
            }}
            .signature-box {{
                text-align: center;
            }}
            .signature-box p {{
                font-size: 13px;
                font-weight: bold;
                margin-bottom: 32px;
            }}
            .signature-line {{
                font-size: 20px;
                border-bottom: 1px solid black;
                padding-bottom: 8px;
                width: 128px;
                margin: 0 auto;
            }}
            section {{
                page-break-inside: avoid;
                margin-bottom: 32px;
            }}
        </style>
    </head>
    <body>
        <!-- Header -->
        <h1>업무 인수인계서</h1>
        <p class="header-date">작성일: {current_date}</p>

        <!-- 1. 기본 정보 -->
        <section>
            <h2>1. 기본 정보</h2>
            <table>
                <tbody>
                    <tr>
                        <th style="width: 96px;">인계자</th>
                        <td>{data.overview.transferor.name or "(이름)"} / {data.overview.transferor.position or "(직급)"}</td>
                        <th style="width: 96px;">인수자</th>
                        <td>{data.overview.transferee.name or "(이름)"} / {data.overview.transferee.position or "(직급)"}</td>
                    </tr>
                    <tr>
                        <th>인계 기간</th>
                        <td colspan="3">{data.overview.period or "-"}</td>
                    </tr>
                    <tr>
                        <th>인계 사유</th>
                        <td colspan="3" style="height: 80px; vertical-align: top;">{data.overview.reason}</td>
                    </tr>
                </tbody>
            </table>
        </section>

        <!-- 2. 직무 개요 -->
        <section>
            <h2>2. 직무 개요</h2>
            <table>
                <tbody>
                    <tr>
                        <th style="width: 128px;">직무명</th>
                        <td>{data.jobStatus.title}</td>
                    </tr>
                    <tr>
                        <th>주요 책임</th>
                        <td>
                            <ul>
                                {responsibilities_html}
                            </ul>
                        </td>
                    </tr>
                </tbody>
            </table>
        </section>

        <!-- 3. 주요 과제 및 현황 -->
        <section>
            <h2>3. 주요 과제 및 현황</h2>
            <table>
                <thead>
                    <tr>
                        <th style="width: 64px;">No</th>
                        <th>과제명</th>
                        <th style="width: 96px;">상태</th>
                        <th style="width: 128px;">기한</th>
                    </tr>
                </thead>
                <tbody>
                    {priorities_rows}
                </tbody>
            </table>
        </section>

        <!-- 4. 진행 중인 프로젝트 -->
        <section>
            <h2>4. 진행 중인 프로젝트</h2>
            <table>
                <thead>
                    <tr>
                        <th>프로젝트명</th>
                        <th style="width: 80px;">담당</th>
                        <th style="width: 64px;">진척도</th>
                        <th>세부 내용</th>
                    </tr>
                </thead>
                <tbody>
                    {projects_rows}
                </tbody>
            </table>
        </section>

        <!-- 5. 리스크 및 참고 문서 -->
        <div class="two-column">
            <div>
                <h2>5. 리스크 및 이슈</h2>
                <div class="border-box">
                    <h4 style="font-weight: bold; text-decoration: underline; margin-bottom: 4px;">현재 이슈:</h4>
                    <p style="margin-bottom: 16px; white-space: pre-wrap;">{data.risks.issues or "없음"}</p>
                    <h4 style="font-weight: bold; text-decoration: underline; margin-bottom: 4px;">잠재적 리스크:</h4>
                    <p style="white-space: pre-wrap;">{data.risks.risks or "없음"}</p>
                </div>
            </div>
            <div>
                <h2>6. 참고 문서</h2>
                <ul class="border-box" style="list-style-type: disc;">
                    {docs_html}
                </ul>
            </div>
        </div>

        <!-- 서명란 -->
        <section class="signature-section">
            <p class="signature-text">
                상기 내용을 정확히 인계하였으며, 인수자는 이를 확인하고 업무를 인수합니다.
            </p>
            <div class="signatures">
                <div class="signature-box">
                    <p>인계자</p>
                    <div class="signature-line">{data.overview.transferor.name or "(서명)"}</div>
                </div>
                <div class="signature-box">
                    <p>인수자</p>
                    <div class="signature-line">{data.overview.transferee.name or "(서명)"}</div>
                </div>
                <div class="signature-box">
                    <p>확인자 (부서장)</p>
                    <div class="signature-line">{data.stakeholders.manager or "(서명)"}</div>
                </div>
            </div>
        </section>
    </body>
    </html>
    """

    return html_content


@router.post("/api/generate-pdf")
async def generate_pdf(data: HandoverData):
    """
    HandoverData를 받아서 PDF를 생성하고 바이너리로 반환
    """
    try:
        # HTML 생성
        html_content = generate_pdf_html(data)

        # WeasyPrint로 PDF 생성
        pdf_buffer = io.BytesIO()
        HTML(string=html_content).write_pdf(pdf_buffer)
        pdf_buffer.seek(0)

        # PDF 파일명 생성
        filename = f"handover_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        # PDF 응답 반환
        return Response(
            content=pdf_buffer.getvalue(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF 생성 실패: {str(e)}")
