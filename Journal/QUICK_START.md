# Quick Start Guide - Journal Paper

## 🚀 Getting Started TODAY

### Step 1: Install Dependencies (5 minutes)
```bash
cd D:\ExplainNet
.\venv\Scripts\Activate.ps1
pip install -r Journal\scripts\requirements_research.txt
```

### Step 2: Review Guidelines (15 minutes)
Read: `Journal\data\ANNOTATION_GUIDELINES.md`

### Step 3: Verify Topics (2 minutes)
```bash
python Journal\scripts\01_topic_selection.py
```

### Step 4: Test Data Collection (1 hour)
Edit `02_data_collection.py` to test with 2 topics first:
```python
# Line 115: Change to test mode
for domain, topics in RESEARCH_TOPICS.items():
    for topic in topics[:1]:  # Only first topic per domain
```

Then run:
```bash
python Journal\scripts\02_data_collection.py
```

---

## 📊 Week 1 Goals (This Week)

- [ ] Install all dependencies
- [ ] Test collection on 5 topics
- [ ] Read 3 survey papers
- [ ] Practice annotating 10 videos
- [ ] Calculate your annotation speed (minutes per video)

**Target**: By Sunday, you should have tested the full pipeline

---

## ⚡ Quick Commands Reference

```bash
# Activate environment
.\venv\Scripts\Activate.ps1

# View topics
python Journal\scripts\01_topic_selection.py

# Collect data (full run - takes ~8 hours)
python Journal\scripts\02_data_collection.py

# Annotate videos
python Journal\scripts\03_annotation_tool.py

# Setup models (Week 5)
python Journal\scripts\04_setup_models.py

# Check progress anytime
# Just open: Journal\PROJECT_TRACKER.md
```

---

## 📁 Folder Organization

```
Journal/
├── README.md               ← Project overview
├── PROJECT_TRACKER.md      ← Detailed week-by-week plan
├── data/
│   ├── ANNOTATION_GUIDELINES.md
│   ├── research_dataset_raw.json        (after Week 2-3)
│   └── research_dataset_annotated.json  (after Week 4)
├── scripts/
│   ├── requirements_research.txt
│   ├── 01_topic_selection.py
│   ├── 02_data_collection.py
│   ├── 03_annotation_tool.py
│   └── 04_setup_models.py
├── models/                  (Week 5+)
├── results/                 (Week 8+)
├── paper/
│   ├── paper.tex
│   └── references.bib
└── literature/
    └── LITERATURE_REVIEW.md
```

**Keep it clean** - No unnecessary files!

---

## 🎯 Critical Success Factors

1. **Consistency**: Work 20-25 hours/week, every week
2. **Save everything**: Git commit daily
3. **Document as you go**: Update PROJECT_TRACKER.md weekly
4. **Ask for help**: When stuck > 2 hours on something
5. **Stay organized**: One folder for everything

---

## 🆘 Troubleshooting

**Q: Data collection fails?**
A: Check API quotas (YouTube: 10K units/day, News: 100 req/day)

**Q: Annotation tool crashes?**
A: Progress is auto-saved after each video in `research_dataset_annotated.json`

**Q: GPU not recognized?**
A: Models will run on CPU (slower but fine for 125 videos)

**Q: Can't find enough papers?**
A: Use Google Scholar filters: 2020-2025, sort by citations

---

## 📞 When to Reach Out

- After Week 1: Share test results
- After Week 4: Share annotation stats (kappa score)
- After Week 8: Share baseline comparison table
- After Week 11: Share paper draft

---

## 🎓 Learning Resources

**Sentiment Analysis**:
- VADER paper: https://www.aaai.org/ocs/index.php/ICWSM/ICWSM14/paper/view/8109
- HuggingFace course: https://huggingface.co/course/chapter1/1

**Academic Writing**:
- How to write a research paper: https://www.nature.com/articles/d41586-019-02918-5
- LaTeX tutorial: https://www.overleaf.com/learn

**Statistics**:
- Understanding p-values: https://www.statisticshowto.com/probability-and-statistics/statistics-definitions/p-value/

---

**You're all set! Start with Step 1 above.** 🚀
