"""
models.py
---------
โครงสร้างข้อมูล (dataclasses) ของเนื้อหาเกม แยกออกมาจาก content.py
เพื่อให้ไฟล์คลังโจทย์ (bank_*.py) import ไปใช้ได้โดยไม่เกิด import วนกัน
(โค้ดเดิมยังเรียก content.Question / content.Lesson ... ได้เหมือนเดิม เพราะ content.py import กลับมาให้)
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Question:
    id: str
    qtype: str  # "mcq" | "word_order" | "translate_type" | "listen_mcq" (ฟังแล้วเลือก) | "listen_type" (ฟังแล้วพิมพ์ตาม)
    prompt: str
    correct_answer: str
    options: List[str] = field(default_factory=list)   # ใช้กับ mcq
    word_bank: List[str] = field(default_factory=list)  # ใช้กับ word_order (คำแบบสับ)
    explanation: str = ""
    vocab: Optional[str] = None  # คำศัพท์ที่ผู้เรียนจะได้จากข้อนี้ (โชว์ในหน้าสรุป)
    alt_answers: List[str] = field(default_factory=list)  # คำตอบอื่นที่ถือว่าถูกเหมือนกัน (ใช้กับ translate_type / word_order)
    prompt_lang: str = "th"  # ภาษาของโจทย์: "th" (ไทย) | "en" (อังกฤษ) ใช้เลือกเสียงอ่านโจทย์และข้อความบนหน้าจอ
    audio_text: str = ""     # ข้อความภาษาอังกฤษที่เกมอ่านออกเสียงให้ฟัง (ใช้กับ listen_mcq / listen_type เท่านั้น)
    difficulty: int = 0      # ระดับความยากสำหรับโหมดจับเวลา 1..DIFFICULTY_LEVELS (0 = ให้ระบบคำนวณอัตโนมัติ)


@dataclass
class Lesson:
    id: str
    title: str
    question_ids: List[str]


@dataclass
class Unit:
    id: str
    title: str
    subtitle: str
    lessons: List[Lesson]
    bg_top: tuple = (255, 255, 255)     # สีพาสเทลประจำ Unit (ใช้เป็นป้ายในหน้าเส้นทางเรียน) - ถูกคำนวณทับอัตโนมัติท้ายไฟล์
    bg_bottom: tuple = (235, 235, 235)  # สีล่างของสีประจำ Unit - ถูกคำนวณทับอัตโนมัติท้ายไฟล์


@dataclass
class Achievement:
    id: str
    title: str
    description: str
    icon: str  # ใช้ชื่อสั้น ๆ ให้ mascot.py วาดไอคอนที่ตรงกัน
