# app/services/pdf_service.py

import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from PyPDF2 import PdfWriter, PdfReader


def register_korean_font():
    """한글 폰트 등록 (시스템에 설치된 나눔고딕 사용)"""
    try:
        # Linux 시스템 폰트 경로
        pdfmetrics.registerFont(TTFont('NanumGothic', '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'))
        pdfmetrics.registerFont(TTFont('NanumGothicBold', '/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf'))
    except:
        try:
            # Mac 시스템 폰트 경로
            pdfmetrics.registerFont(TTFont('NanumGothic', '/Library/Fonts/NanumGothic.ttf'))
            pdfmetrics.registerFont(TTFont('NanumGothicBold', '/Library/Fonts/NanumGothicBold.ttf'))
        except:
            # 폰트를 찾을 수 없는 경우 기본 폰트 사용 (한글 깨짐 가능)
            print("⚠️ 나눔고딕 폰트를 찾을 수 없습니다. 기본 폰트를 사용합니다.")


def create_handover_pdf(handover_data: dict) -> bytes:
    """
    인수인계서 데이터를 받아 PDF를 생성하고 bytes로 반환

    Args:
        handover_data: HandoverData 구조의 딕셔너리

    Returns:
        PDF 파일의 bytes
    """
    # 한글 폰트 등록
    register_korean_font()

    # PDF 버퍼 생성
    buffer = io.BytesIO()

    # PDF 문서 생성 (A4 사이즈, 여백 10mm)
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=10*mm,
        leftMargin=10*mm,
        topMargin=15*mm,
        bottomMargin=15*mm
    )

    # 스타일 정의
    styles = getSampleStyleSheet()

    # 한글 스타일 추가
    title_style = ParagraphStyle(
        'KoreanTitle',
        parent=styles['Heading1'],
        fontName='NanumGothicBold',
        fontSize=18,
        alignment=TA_CENTER,
        spaceAfter=12,
        textColor=colors.HexColor('#1a1a1a')
    )

    heading_style = ParagraphStyle(
        'KoreanHeading',
        parent=styles['Heading2'],
        fontName='NanumGothicBold',
        fontSize=14,
        spaceBefore=12,
        spaceAfter=6,
        textColor=colors.HexColor('#2563eb')
    )

    normal_style = ParagraphStyle(
        'KoreanNormal',
        parent=styles['Normal'],
        fontName='NanumGothic',
        fontSize=10,
        leading=14
    )

    small_style = ParagraphStyle(
        'KoreanSmall',
        parent=styles['Normal'],
        fontName='NanumGothic',
        fontSize=9,
        leading=12
    )

    # PDF 컨텐츠 구성
    story = []

    # 제목
    story.append(Paragraph("업무 인수인계서", title_style))
    story.append(Spacer(1, 10*mm))

    # 1. 개요 (Overview)
    if handover_data.get('overview'):
        overview = handover_data['overview']
        story.append(Paragraph("1. 인수인계 개요", heading_style))

        # 기본 정보 테이블
        data = []

        # 인계자 정보
        transferor = overview.get('transferor', {})
        if transferor:
            data.append(['인계자', f"{transferor.get('name', '')} ({transferor.get('position', '')})",
                        '연락처', transferor.get('contact', '')])

        # 인수자 정보
        transferee = overview.get('transferee', {})
        if transferee:
            data.append(['인수자', f"{transferee.get('name', '')} ({transferee.get('position', '')})",
                        '연락처', transferee.get('contact', '')])
            if transferee.get('startDate'):
                data.append(['인수 시작일', transferee.get('startDate', ''), '', ''])

        # 기타 정보
        if overview.get('period'):
            data.append(['근무 기간', overview.get('period', ''), '', ''])
        if overview.get('reason'):
            data.append(['인수인계 사유', overview.get('reason', ''), '', ''])

        if data:
            table = Table(data, colWidths=[30*mm, 60*mm, 25*mm, 65*mm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f4f6')),
                ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#f3f4f6')),
                ('FONT', (0, 0), (-1, -1), 'NanumGothic', 9),
                ('FONTNAME', (0, 0), (0, -1), 'NanumGothicBold'),
                ('FONTNAME', (2, 0), (2, -1), 'NanumGothicBold'),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            story.append(table)

        # 업무 배경
        if overview.get('background'):
            story.append(Spacer(1, 5*mm))
            story.append(Paragraph("<b>업무 배경</b>", normal_style))
            story.append(Paragraph(overview.get('background', ''), normal_style))

        story.append(Spacer(1, 8*mm))

    # 2. 직무 현황 (Job Status)
    if handover_data.get('jobStatus'):
        job_status = handover_data['jobStatus']
        story.append(Paragraph("2. 직무 현황", heading_style))

        data = []
        if job_status.get('title'):
            data.append(['직책', job_status.get('title', '')])
        if job_status.get('authority'):
            data.append(['권한', job_status.get('authority', '')])
        if job_status.get('reportingLine'):
            data.append(['보고 체계', job_status.get('reportingLine', '')])
        if job_status.get('teamMission'):
            data.append(['팀 미션', job_status.get('teamMission', '')])

        if data:
            table = Table(data, colWidths=[30*mm, 150*mm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f4f6')),
                ('FONT', (0, 0), (-1, -1), 'NanumGothic', 9),
                ('FONTNAME', (0, 0), (0, -1), 'NanumGothicBold'),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            story.append(table)

        # 책임 사항
        if job_status.get('responsibilities'):
            story.append(Spacer(1, 5*mm))
            story.append(Paragraph("<b>주요 책임</b>", normal_style))
            for resp in job_status.get('responsibilities', []):
                story.append(Paragraph(f"• {resp}", normal_style))

        # 팀 목표
        if job_status.get('teamGoals'):
            story.append(Spacer(1, 5*mm))
            story.append(Paragraph("<b>팀 목표</b>", normal_style))
            for goal in job_status.get('teamGoals', []):
                story.append(Paragraph(f"• {goal}", normal_style))

        story.append(Spacer(1, 8*mm))

    # 3. 우선 과제 (Priorities)
    if handover_data.get('priorities') and len(handover_data.get('priorities', [])) > 0:
        story.append(Paragraph("3. 우선 과제", heading_style))

        priorities = handover_data.get('priorities', [])
        data = [['순위', '과제명', '상태', '해결방안', '마감일']]

        for priority in priorities:
            data.append([
                str(priority.get('rank', '')),
                priority.get('title', ''),
                priority.get('status', ''),
                priority.get('solution', ''),
                priority.get('deadline', '')
            ])

        table = Table(data, colWidths=[15*mm, 50*mm, 25*mm, 50*mm, 25*mm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONT', (0, 0), (-1, 0), 'NanumGothicBold', 9),
            ('FONT', (0, 1), (-1, -1), 'NanumGothic', 8),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (1, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(table)
        story.append(Spacer(1, 8*mm))

    # 4. 관계자 정보 (Stakeholders)
    if handover_data.get('stakeholders'):
        stakeholders = handover_data['stakeholders']
        story.append(Paragraph("4. 주요 관계자", heading_style))

        if stakeholders.get('manager'):
            story.append(Paragraph(f"<b>상급자:</b> {stakeholders.get('manager', '')}", normal_style))
            story.append(Spacer(1, 3*mm))

        # 내부 관계자
        if stakeholders.get('internal') and len(stakeholders.get('internal', [])) > 0:
            story.append(Paragraph("<b>내부 관계자</b>", normal_style))
            data = [['이름', '역할']]
            for person in stakeholders.get('internal', []):
                data.append([person.get('name', ''), person.get('role', '')])

            table = Table(data, colWidths=[50*mm, 115*mm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
                ('FONT', (0, 0), (-1, -1), 'NanumGothic', 9),
                ('FONTNAME', (0, 0), (-1, 0), 'NanumGothicBold'),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            story.append(table)
            story.append(Spacer(1, 5*mm))

        # 외부 관계자
        if stakeholders.get('external') and len(stakeholders.get('external', [])) > 0:
            story.append(Paragraph("<b>외부 관계자</b>", normal_style))
            data = [['이름', '역할']]
            for person in stakeholders.get('external', []):
                data.append([person.get('name', ''), person.get('role', '')])

            table = Table(data, colWidths=[50*mm, 115*mm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
                ('FONT', (0, 0), (-1, -1), 'NanumGothic', 9),
                ('FONTNAME', (0, 0), (-1, 0), 'NanumGothicBold'),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            story.append(table)

        story.append(Spacer(1, 8*mm))

    # 5. 팀원 정보 (Team Members)
    if handover_data.get('teamMembers') and len(handover_data.get('teamMembers', [])) > 0:
        story.append(Paragraph("5. 팀원 정보", heading_style))

        data = [['이름', '직급', '역할', '비고']]
        for member in handover_data.get('teamMembers', []):
            data.append([
                member.get('name', ''),
                member.get('position', ''),
                member.get('role', ''),
                member.get('notes', '')
            ])

        table = Table(data, colWidths=[35*mm, 30*mm, 60*mm, 40*mm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONT', (0, 0), (-1, 0), 'NanumGothicBold', 9),
            ('FONT', (0, 1), (-1, -1), 'NanumGothic', 8),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(table)
        story.append(Spacer(1, 8*mm))

    # 6. 진행 중인 프로젝트 (Ongoing Projects)
    if handover_data.get('ongoingProjects') and len(handover_data.get('ongoingProjects', [])) > 0:
        story.append(Paragraph("6. 진행 중인 프로젝트", heading_style))

        for project in handover_data.get('ongoingProjects', []):
            story.append(Paragraph(f"<b>{project.get('name', '')}</b>", normal_style))

            project_data = []
            if project.get('owner'):
                project_data.append(['담당자', project.get('owner', '')])
            if project.get('status'):
                project_data.append(['상태', project.get('status', '')])
            if project.get('progress') is not None:
                project_data.append(['진행률', f"{project.get('progress', 0)}%"])
            if project.get('deadline'):
                project_data.append(['마감일', project.get('deadline', '')])
            if project.get('description'):
                project_data.append(['설명', project.get('description', '')])

            if project_data:
                table = Table(project_data, colWidths=[30*mm, 135*mm])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f4f6')),
                    ('FONT', (0, 0), (-1, -1), 'NanumGothic', 9),
                    ('FONTNAME', (0, 0), (0, -1), 'NanumGothicBold'),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('LEFTPADDING', (0, 0), (-1, -1), 5),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                    ('TOPPADDING', (0, 0), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ]))
                story.append(table)
                story.append(Spacer(1, 5*mm))

        story.append(Spacer(1, 3*mm))

    # 7. 리스크 및 이슈 (Risks)
    if handover_data.get('risks'):
        risks = handover_data['risks']
        story.append(Paragraph("7. 리스크 및 이슈", heading_style))

        if risks.get('issues'):
            story.append(Paragraph("<b>현안 사항</b>", normal_style))
            story.append(Paragraph(risks.get('issues', ''), normal_style))
            story.append(Spacer(1, 3*mm))

        if risks.get('risks'):
            story.append(Paragraph("<b>위험 요소</b>", normal_style))
            story.append(Paragraph(risks.get('risks', ''), normal_style))

        story.append(Spacer(1, 8*mm))

    # 8. 리소스 (Resources)
    if handover_data.get('resources'):
        resources = handover_data['resources']
        story.append(Paragraph("8. 주요 리소스", heading_style))

        # 문서
        if resources.get('docs') and len(resources.get('docs', [])) > 0:
            story.append(Paragraph("<b>문서</b>", normal_style))
            data = [['분류', '문서명', '위치']]
            for doc in resources.get('docs', []):
                data.append([
                    doc.get('category', ''),
                    doc.get('name', ''),
                    doc.get('location', '')
                ])

            table = Table(data, colWidths=[30*mm, 60*mm, 75*mm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
                ('FONT', (0, 0), (-1, -1), 'NanumGothic', 8),
                ('FONTNAME', (0, 0), (-1, 0), 'NanumGothicBold'),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            story.append(table)
            story.append(Spacer(1, 5*mm))

        # 시스템
        if resources.get('systems') and len(resources.get('systems', [])) > 0:
            story.append(Paragraph("<b>시스템</b>", normal_style))
            data = [['시스템명', '사용 방법', '담당자']]
            for system in resources.get('systems', []):
                data.append([
                    system.get('name', ''),
                    system.get('usage', ''),
                    system.get('contact', '')
                ])

            table = Table(data, colWidths=[40*mm, 80*mm, 45*mm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
                ('FONT', (0, 0), (-1, -1), 'NanumGothic', 8),
                ('FONTNAME', (0, 0), (-1, 0), 'NanumGothicBold'),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            story.append(table)
            story.append(Spacer(1, 5*mm))

        # 연락처
        if resources.get('contacts') and len(resources.get('contacts', [])) > 0:
            story.append(Paragraph("<b>주요 연락처</b>", normal_style))
            data = [['분류', '이름', '직급', '연락처']]
            for contact in resources.get('contacts', []):
                data.append([
                    contact.get('category', ''),
                    contact.get('name', ''),
                    contact.get('position', ''),
                    contact.get('contact', '')
                ])

            table = Table(data, colWidths=[25*mm, 40*mm, 40*mm, 60*mm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
                ('FONT', (0, 0), (-1, -1), 'NanumGothic', 8),
                ('FONTNAME', (0, 0), (-1, 0), 'NanumGothicBold'),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            story.append(table)

        story.append(Spacer(1, 8*mm))

    # 9. 체크리스트 (Checklist)
    if handover_data.get('checklist') and len(handover_data.get('checklist', [])) > 0:
        story.append(Paragraph("9. 인수인계 체크리스트", heading_style))

        for item in handover_data.get('checklist', []):
            checkbox = '☑' if item.get('completed', False) else '☐'
            story.append(Paragraph(f"{checkbox} {item.get('text', '')}", normal_style))

        story.append(Spacer(1, 10*mm))

    # 서명란
    story.append(PageBreak())
    story.append(Spacer(1, 20*mm))
    story.append(Paragraph("확인 및 서명", heading_style))
    story.append(Spacer(1, 10*mm))

    signature_data = [
        ['', '성명', '서명', '날짜'],
        ['인계자', '', '', ''],
        ['인수자', '', '', ''],
        ['승인자', '', '', '']
    ]

    signature_table = Table(signature_data, colWidths=[30*mm, 50*mm, 50*mm, 50*mm])
    signature_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
        ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#f3f4f6')),
        ('FONT', (0, 0), (-1, -1), 'NanumGothic', 10),
        ('FONTNAME', (0, 0), (-1, 0), 'NanumGothicBold'),
        ('FONTNAME', (0, 1), (0, -1), 'NanumGothicBold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (1, 1), (-1, -1), [colors.white]),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
    ]))
    story.append(signature_table)

    # 생성일
    story.append(Spacer(1, 15*mm))
    creation_date = datetime.now().strftime('%Y년 %m월 %d일')
    story.append(Paragraph(f"<para alignment='center'>작성일: {creation_date}</para>", normal_style))

    # PDF 생성
    doc.build(story)

    # PyPDF2를 사용하여 메타데이터 추가
    buffer.seek(0)
    pdf_reader = PdfReader(buffer)
    pdf_writer = PdfWriter()

    # 모든 페이지 복사
    for page in pdf_reader.pages:
        pdf_writer.add_page(page)

    # 메타데이터 추가
    pdf_writer.add_metadata({
        '/Title': '업무 인수인계서',
        '/Author': 'Handover System',
        '/Subject': 'Business Handover Document',
        '/Creator': 'Handover PDF Generator',
        '/Producer': 'PyPDF2 + ReportLab',
        '/CreationDate': datetime.now().strftime('D:%Y%m%d%H%M%S')
    })

    # 최종 PDF 생성
    final_buffer = io.BytesIO()
    pdf_writer.write(final_buffer)
    final_buffer.seek(0)

    return final_buffer.getvalue()


def save_pdf_to_blob(pdf_bytes: bytes, filename: str, user_id: str = None) -> str:
    """
    생성된 PDF를 Azure Blob Storage에 저장

    Args:
        pdf_bytes: PDF 파일의 bytes
        filename: 저장할 파일명
        user_id: 사용자 ID (선택사항)

    Returns:
        저장된 파일의 URL
    """
    from app.services.blob_service import upload_to_blob

    # user_id가 있으면 경로에 포함
    if user_id:
        full_filename = f"handovers/{user_id}/{filename}"
    else:
        full_filename = f"handovers/{filename}"

    # Blob에 업로드 (blob_service의 시그니처에 맞춤)
    blob_url = upload_to_blob(full_filename, pdf_bytes, index_name=None)

    return blob_url
