# Journal Paper Project Tracker

## Timeline: Dec 2025 - Feb 2026 (12 weeks)

---

## MONTH 1: Dataset Creation ✓ Setup Complete

### Week 1: Planning & Setup (Dec 1-7)
- [x] Create Journal folder structure
- [x] Define 25 research topics
- [x] Write annotation guidelines
- [ ] Review guidelines with mentor/peer
- [ ] Run topic selection script
- [ ] Test data collection on 2 topics

### Week 2-3: Data Collection (Dec 8-21)
- [ ] Run automated collection for all 25 topics
- [ ] Expected: 125 videos, 250+ articles
- [ ] Verify all transcripts extracted
- [ ] Export to JSON format
- [ ] Backup data (3 copies)

### Week 4: Manual Annotation (Dec 22-31)
- [ ] Day 1-2: Annotate 30 videos (warmup)
- [ ] Day 3-4: Annotate 30 videos
- [ ] Day 5-6: Annotate 30 videos  
- [ ] Day 7-8: Annotate 35 videos (finish)
- [ ] Re-annotate 20 random videos
- [ ] Calculate inter-annotator kappa (target > 0.65)

**Deliverable**: `research_dataset_annotated.json` with 125 annotated videos

---

## MONTH 2: Novel Methodology

### Week 5: Open-Source Models (Jan 1-7)
- [ ] Install transformers, torch, sklearn
- [ ] Download RoBERTa sentiment model
- [ ] Download DistilBERT sentiment model
- [ ] Download emotion classification model
- [ ] Test all models on GPU
- [ ] Re-analyze all 125 videos with new models
- [ ] Compare predictions with manual annotations

### Week 6: Meta-Learner (Jan 8-14)
- [ ] Extract 25+ features per video
- [ ] Create feature matrix (125 x 25)
- [ ] Split data: 80% train, 20% test
- [ ] Train Random Forest meta-classifier
- [ ] 5-fold cross-validation
- [ ] Analyze feature importance
- [ ] Save trained model

### Week 7: Divergence Metric (Jan 15-21)
- [ ] Calculate sentiment for news articles
- [ ] Define SDS formula mathematically
- [ ] Compute SDS for all 125 videos
- [ ] Correlate with credibility labels
- [ ] ROC curve analysis
- [ ] Chi-square significance test
- [ ] Document findings

### Week 8: Baseline Comparisons (Jan 22-31)
- [ ] Implement VADER-only baseline
- [ ] Implement RoBERTa-only baseline
- [ ] Implement DistilBERT-only baseline
- [ ] Implement simple averaging ensemble
- [ ] Implement weighted voting ensemble
- [ ] Calculate all metrics (accuracy, P/R/F1, kappa)
- [ ] Run paired t-tests (meta-learner vs each baseline)
- [ ] Create comparison table
- [ ] Generate confusion matrices

**Deliverable**: Trained meta-learner + complete results tables

---

## MONTH 3: Writing & Submission

### Week 9: Literature Review (Feb 1-7)
- [ ] Day 1: Survey papers (5 papers)
- [ ] Day 2: Sentiment methods (10 papers)
- [ ] Day 3: YouTube/video (10 papers)
- [ ] Day 4: Ensemble methods (8 papers)
- [ ] Day 5: Cross-platform (5 papers)
- [ ] Day 6: Misinformation (5 papers)
- [ ] Day 7: Organize citations in Zotero
- [ ] Write research gap paragraph

### Week 10: Paper Writing Part 1 (Feb 8-14)
- [ ] Day 1-2: Introduction (1.5 pages)
- [ ] Day 3-4: Related Work (2 pages, cite 30 papers)
- [ ] Day 5-6: Methodology Section 3.1-3.2 (1.5 pages)
- [ ] Day 7: Methodology Section 3.3-3.4 (1.5 pages)

### Week 11: Paper Writing Part 2 (Feb 15-21)
- [ ] Day 1-2: Experiments & Results (2.5 pages)
- [ ] Day 3: Discussion (1.5 pages)
- [ ] Day 4: Limitations & Conclusion (1 page)
- [ ] Day 5: Create all figures (matplotlib)
- [ ] Day 6: Format all tables (LaTeX)
- [ ] Day 7: Polish, proofread

### Week 12: Submission (Feb 22-28)
- [ ] Day 1: Clean GitHub repo
- [ ] Day 2: Write comprehensive README
- [ ] Day 3: Upload dataset to Zenodo (get DOI)
- [ ] Day 4: Format paper in LaTeX
- [ ] Day 5: Run Grammarly, final checks
- [ ] Day 6: Write cover letter
- [ ] Day 7: **SUBMIT TO PEERJ**

**Deliverable**: Submitted paper + public dataset + code release

---

## Key Files to Create

### Scripts (in Journal/scripts/)
- [x] 01_topic_selection.py
- [x] 02_data_collection.py
- [x] 03_annotation_tool.py
- [x] 04_setup_models.py
- [ ] 05_run_sentiment_analysis.py
- [ ] 06_extract_features.py
- [ ] 07_train_metalearner.py
- [ ] 08_calculate_divergence.py
- [ ] 09_baseline_comparison.py
- [ ] 10_generate_figures.py
- [ ] 11_statistical_tests.py

### Data Files (in Journal/data/)
- [x] ANNOTATION_GUIDELINES.md
- [ ] research_dataset_raw.json (from script 02)
- [ ] research_dataset_annotated.json (from script 03)
- [ ] features_matrix.csv (from script 06)
- [ ] sentiment_predictions.csv (from script 05)

### Results (in Journal/results/)
- [ ] baseline_comparison.csv
- [ ] confusion_matrices.png
- [ ] feature_importance.png
- [ ] roc_curves.png
- [ ] divergence_distribution.png

### Paper (in Journal/paper/)
- [x] paper.tex
- [x] references.bib
- [ ] All figures (.pdf or .png)

---

## Success Metrics

### Dataset Quality
- ✅ 125 videos annotated
- ✅ Inter-annotator kappa > 0.65
- ✅ All 6 emotions rated
- ✅ Credibility labels complete

### Model Performance
- ✅ Meta-learner accuracy > 75%
- ✅ Beats best baseline by > 3%
- ✅ Statistical significance (p < 0.05)
- ✅ Feature importance interpretable

### Paper Quality
- ✅ 30+ citations
- ✅ Clear research gap identified
- ✅ All figures publication-ready
- ✅ Code & data publicly available

### Submission Target
- **Primary**: PeerJ Computer Science
- **Backup**: SoftwareX, JOSS
- **Acceptance probability**: 60-70%

---

## Weekly Time Commitment

| Week | Focus | Hours/Week |
|------|-------|------------|
| 1 | Planning | 15 |
| 2-3 | Data collection | 20 |
| 4 | Annotation | 45 |
| 5 | Models | 25 |
| 6 | Meta-learner | 30 |
| 7 | Divergence | 20 |
| 8 | Baselines | 25 |
| 9 | Literature | 30 |
| 10-11 | Writing | 50 |
| 12 | Submission | 20 |

**Total**: ~280 hours over 12 weeks

---

## Next Actions (START HERE)

1. **Review annotation guidelines** (Journal/data/ANNOTATION_GUIDELINES.md)
2. **Run topic selection**: `python Journal/scripts/01_topic_selection.py`
3. **Test data collection**: Modify script for 2 topics first
4. **Set calendar reminders** for each week's milestones
5. **Install research dependencies**: `pip install -r Journal/scripts/requirements_research.txt`

---

## Emergency Contacts & Resources

- **Mentor**: [Your mentor's contact]
- **GitHub repo**: https://github.com/aryajayasankar/ExplainNet
- **PeerJ submission**: https://peerj.com/computer-science/
- **Zotero**: https://www.zotero.org/
- **Overleaf**: https://www.overleaf.com/

---

*Last updated: December 1, 2025*
