# 🎓 EduAssistant — 강의 자동 전사 및 문제 생성 서비스

> 강의 오디오를 실시간으로 캡처하여 텍스트로 전사하고,  
> LLM이 자동으로 학습 문제를 생성해주는 교육 보조 서비스

![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-000000?style=flat)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat&logo=postgresql&logoColor=white)

---

## 📌 문제 정의

- 강의를 들으면서 핵심 내용을 정리하고 문제를 만드는 작업은 시간이 많이 소요되고 학습 집중도를 떨어뜨림
- 강의 내용을 기반으로 자동으로 문제를 생성하면 복습 효율을 높일 수 있다고 판단

---

## 🏗 서비스 아키텍처

    웹 브라우저 오디오 캡처
            ↓
       WhisperX 전사
            ↓
      PostgreSQL DB 적재
            ↓
    LangChain + Qwen LLM
            ↓
       학습 문제 생성
            ↓
       FastAPI 응답

---

## 🛠 기술 스택

| 분류 | 기술 |
|------|------|
| 백엔드 | FastAPI |
| AI 파이프라인 | LangChain, Qwen |
| 음성 처리 | WhisperX |
| DB | PostgreSQL, Alembic |
| 배포 | Docker, docker-compose |

---

## 🔍 주요 구현 내용

**1. 실시간 오디오 캡처 및 전사**
- 웹 브라우저에서 강의 오디오를 실시간 캡처
- WhisperX를 활용하여 음성을 텍스트로 자동 전사

**2. 데이터 적재 및 관리**
- 전사된 텍스트를 PostgreSQL DB에 구조화하여 적재
- Alembic 기반 DB 마이그레이션으로 스키마 버전 관리

**3. LLM 기반 문제 생성**
- LangChain + Qwen을 활용하여 전사 텍스트 기반 학습 문제 자동 생성
- 강의 내용에 맞는 질문·답변 구조로 출력

---

## 🚀 실행 방법

    git clone https://github.com/Kim-gami/edu_assistant
    cd edu_assistant
    cp .env.example .env
    docker-compose up

---

## 👤 개발

- 1인 개발 프로젝트
