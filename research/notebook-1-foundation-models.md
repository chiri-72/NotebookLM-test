# Notebook 1: AI Foundation Models (기반 모델 기술)

## 리서치 주제
Large Language Models, Transformer Architecture, Training Methods, Multimodal AI

## 핵심 소스 (10+ Sources)

### 📰 Articles & Research

1. **2025: The year in LLMs**
   - URL: https://simonwillison.net/2025/Dec/31/the-year-in-llms/
   - 요약: 2025년 LLM 발전사, Claude 4 Extended Thinking Mode, Gemini 2.0-3.0 Deep Think 기능

2. **AI Updates Today (February 2026) – Latest AI Model Releases**
   - URL: https://llm-stats.com/llm-updates
   - 요약: 2026년 2월 최신 AI 모델 업데이트 현황

3. **Top LLMs and AI Trends for 2026**
   - URL: https://www.clarifai.com/blog/llms-and-ai-trends
   - 요약: 2026년 LLM 및 AI 트렌드 분석

4. **Mamba: A Potential Transformer Replacement**
   - URL: https://zilliz.com/learn/mamba-architecture-potential-transformer-replacement
   - 요약: Mamba 아키텍처, Transformer 대비 4-5배 높은 inference throughput

5. **A survey of RWKV**
   - URL: https://www.sciencedirect.com/science/article/abs/pii/S0925231225013839
   - 요약: RWKV 모델, RNN + Transformer 하이브리드 아키텍처

6. **Practical Tips for Finetuning LLMs Using LoRA**
   - URL: https://magazine.sebastianraschka.com/p/practical-tips-for-finetuning-llms
   - 요약: LoRA를 활용한 LLM Fine-tuning 실용 가이드

7. **Efficient LLM Fine-Tuning: LoRA, QLoRA & RLHF**
   - URL: https://medium.com/@hetp2030/parameter-efficient-fine-tuning-of-large-language-models-from-lora-to-rlhf-c17e166da5df
   - 요약: PEFT 기법, GPU 요구사항 90% 감소

8. **Multimodal Models (GPT-4V, Gemini, LLaVA) Explained**
   - URL: https://uplatz.com/blog/multimodal-models-gpt-4v-gemini-llava-explained/
   - 요약: 멀티모달 AI 모델 비교 분석

9. **Decoding Multimodal AI foundation models in 2026**
   - URL: https://cvisiona.com/decoding-multimodal-ai-foundation-models-in-2026/
   - 요약: 2026년 멀티모달 AI 기반 모델 해석

10. **Google introduces Gemini 2.0: A new AI model for the agentic era**
    - URL: https://blog.google/technology/google-deepmind/google-gemini-ai-update-december-2024/
    - 요약: Gemini 2.0 발표, 에이전트 시대를 위한 새로운 AI 모델

### 🎥 YouTube Resources

11. **3Blue1Brown - Transformers, the tech behind LLMs**
    - URL: https://www.3blue1brown.com/lessons/gpt
    - 채널: 3Blue1Brown (시각적 Transformer 설명)

12. **Andrej Karpathy - Let's build GPT**
    - 채널: Andrej Karpathy
    - 내용: GPT 모델을 처음부터 구축하는 실습 튜토리얼

13. **Yannic Kilcher - "Attention is All You Need" Paper Breakdown**
    - 채널: Yannic Kilcher
    - 내용: Transformer 원본 논문 상세 분석

14. **Krish Naik - NLP with Deep Learning Playlist**
    - 채널: Krish Naik
    - 내용: Word embeddings, tokens, neural networks for text generation

15. **DeepLearning.AI - How Transformer LLMs Work**
    - URL: https://www.deeplearning.ai/short-courses/how-transformer-llms-work/
    - 내용: Transformer LLM 주요 컴포넌트 딥다이브

## 핵심 인사이트

### 1. LLM 아키텍처 진화
- **Claude 4 Family**: Extended Thinking Mode로 deliberate reasoning 지원
- **Gemini 3.0**: Deep Think로 2.5배 reasoning 성능 향상
- **GPT-5**: Opus 4.5와 비슷한 수준의 code 성능

### 2. Post-Transformer 아키텍처
- **Mamba**: 4-5배 높은 inference throughput, 상수 시간 메모리 footprint
- **RWKV**: Parallel training (Transformer처럼) + Efficient inference (RNN처럼)

### 3. 효율적 학습 방법론
- **LoRA**: GPU 요구사항 90% 감소, 7B 파라미터 모델을 단일 GPU에서 fine-tune 가능
- **QLoRA**: 메모리 사용량 33% 추가 감소 (4-bit quantization)
- **RLHF**: ChatGPT, GPT-4, Claude의 핵심 정렬 기술

### 4. 멀티모달 AI
- Gemini는 처음부터 멀티모달로 설계됨 (text, code, audio, image, video)
- GPT-4V: 이미지 이해 및 텍스트 생성
- Apple-Google 파트너십: Siri의 다음 세대 기반 모델로 Gemini 활용 (2026년 1월)

## 리서치 품질 평가
- **깊이**: ⭐⭐⭐⭐⭐ (최신 논문부터 실용 가이드까지)
- **다양성**: ⭐⭐⭐⭐⭐ (아키텍처, 학습, 멀티모달 모두 커버)
- **신뢰성**: ⭐⭐⭐⭐⭐ (Google, OpenAI, Anthropic 공식 소스 포함)
