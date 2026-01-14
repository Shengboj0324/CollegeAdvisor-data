# Visual Design Guide for Technical Slides

**Purpose**: Instructions for creating visual elements in PowerPoint/Keynote  
**Style**: Clean, technical, data-driven

---

## 🎨 Design Principles

### Color Scheme
- **Primary**: Deep Blue (#1E3A8A) - Architecture, headers
- **Success**: Green (#10B981) - Metrics, checkmarks, positive results
- **Warning**: Amber (#F59E0B) - Alerts, optimizations needed
- **Error**: Red (#EF4444) - Problems, errors (use sparingly)
- **Neutral**: Gray (#6B7280) - Text, secondary info
- **Accent**: Cyan (#06B6D4) - Highlights, citations

### Typography
- **Headers**: Bold, 36-44pt, Deep Blue
- **Body**: Regular, 18-24pt, Dark Gray
- **Code**: Monospace (Courier/Monaco), 14-16pt
- **Numbers**: Bold, 28-32pt for key metrics

### Layout
- **Margins**: 10% on all sides
- **Alignment**: Left-aligned text, centered diagrams
- **Spacing**: 1.5x line height for readability
- **Consistency**: Same layout for similar slide types

---

## 📊 Slide-by-Slide Visual Instructions

### SLIDE 2: System Architecture Overview

**Visual Type**: Layered diagram (4 boxes stacked vertically)

**How to Create**:
1. Insert 4 rectangles, stack vertically with small gaps
2. Color gradient: Darkest (bottom) → Lightest (top)
   - Layer 1 (Knowledge Base): Deep Blue (#1E3A8A)
   - Layer 2 (Retrieval): Medium Blue (#3B82F6)
   - Layer 3 (Synthesis): Light Blue (#60A5FA)
   - Layer 4 (LLM): Cyan (#06B6D4)
3. Add white text inside each box
4. Add arrows between layers (↑ direction)
5. Add metrics on right side with icons

**Icons to Use**:
- 📚 Knowledge Base
- 🔍 Retrieval
- ⚙️ Synthesis
- 💬 LLM

---

### SLIDE 3: Deployment Architecture

**Visual Type**: Cloud infrastructure diagram

**How to Create**:
1. Top: Phone icon (iOS App)
2. Arrow down labeled "HTTPS/REST"
3. Middle: Large rounded rectangle (Google Cloud Run)
4. Inside Cloud Run: 2 smaller boxes
   - FastAPI (left)
   - ProductionRAG (right)
5. Bottom: Database icons (ChromaDB, Ollama)
6. Use cloud icon background (subtle)

**Colors**:
- Phone: Dark gray
- Cloud Run: Google Cloud blue (#4285F4)
- FastAPI: Green (#10B981)
- ProductionRAG: Blue (#3B82F6)
- Databases: Gray (#6B7280)

**Status Badges** (top right):
- ✅ Deployed (green badge)
- ✅ 99.9% Uptime (green badge)

---

### SLIDE 4: Hybrid Retrieval System

**Visual Type**: Venn diagram with performance table

**How to Create**:
1. **Left circle**: BM25 (Blue)
   - List strengths inside
2. **Right circle**: Dense Vectors (Cyan)
   - List strengths inside
3. **Overlap**: RRF Fusion (Purple)
   - Show combined metrics
4. **Below**: Performance comparison table
   - 3 columns: BM25 Only | Dense Only | Hybrid
   - Highlight "Hybrid" column in green

**Formula Box** (bottom):
- Light gray background
- Monospace font
- Show RRF formula

---

### SLIDE 5: Priority-Based Handler Routing

**Visual Type**: Priority table with color coding

**How to Create**:
1. Create table with 4 columns
2. Color-code priority column:
   - 150: Dark red (highest)
   - 145: Red
   - 140: Orange
   - 135: Yellow
   - 125: Light yellow
   - 100: Light green
   - 90: Green
   - 0: Gray (fallback)
3. Add icons for each handler type:
   - 🏠 Foster Care
   - 💰 Financial Aid
   - 🎓 Admissions
   - 🔄 Transfer
   - 🌐 Immigration

**Highlight**: Top 3 handlers (150, 145, 140) with bold text

---

### SLIDE 6: Cite-or-Abstain Policy

**Visual Type**: Flowchart with decision diamond

**How to Create**:
1. **Start**: Query input (rounded rectangle, blue)
2. **Step 1**: Retrieve documents (rectangle, blue)
3. **Step 2**: Construct answer (rectangle, blue)
4. **Step 3**: Validate citations (rectangle, blue)
5. **Decision**: Coverage ≥ 90%? (diamond, amber)
   - **YES** → Return answer (green, checkmark)
   - **NO** → Abstain (red, X)
6. Connect with arrows

**Code Box** (right side):
- Show Python code snippet
- Light gray background
- Syntax highlighting

---

### SLIDE 7: Performance Metrics - Latency

**Visual Type**: Horizontal bar chart (breakdown)

**How to Create**:
1. **Total bar**: 3.5s (full width)
2. **Breakdown** (stacked segments):
   - Retrieval: 1.2s (34%) - Blue
   - Synthesis: 0.8s (23%) - Cyan
   - Generation: 1.5s (43%) - Green
3. **Sub-breakdown** (below each segment):
   - Show component times in smaller text
4. **Comparison** (right side):
   - GPT-4: 5-8s (red bar)
   - Claude: 5-8s (red bar)
   - Our System: 3.5s (green bar, highlighted)

**Labels**: Show percentages and absolute times

---

### SLIDE 8: Performance Metrics - Cost

**Visual Type**: Cost comparison chart

**How to Create**:
1. **Left**: Breakdown table
   - 5 rows (components)
   - 2 columns (Component | Cost)
   - Total row in bold
2. **Right**: Bar chart comparison
   - 4 bars (GPT-4, Claude, Generic RAG, Ours)
   - Height = cost
   - Our bar in green, others in red
   - Show 10x savings annotation

**Callout Box** (bottom):
- "Annual Savings: $21,600"
- Large font, green background

---

### SLIDE 10: Testing Results - Perfect Scores

**Visual Type**: Score breakdown with progress bars

**How to Create**:
1. **Top**: Large "10.0/10.0" (72pt font, green)
2. **Breakdown** (4 progress bars):
   - Factual Accuracy: 80/80 (100% filled, green)
   - Citation Coverage: 60/60 (100% filled, green)
   - Completeness: 40/40 (100% filled, green)
   - Abstention: 20/20 (100% filled, green)
3. **Table** (bottom): Category breakdown
4. **Comparison** (right):
   - GPT-4: 6.5-7.5/10 (red)
   - Claude: 6.5-7.5/10 (red)
   - Generic RAG: 7.5-8.5/10 (amber)
   - Ours: 10.0/10.0 (green, highlighted)

---

### SLIDE 12: Simulation - User Journey

**Visual Type**: Vertical flowchart with timing

**How to Create**:
1. **5 boxes** stacked vertically:
   - iOS App Input (blue)
   - Backend Processing (cyan)
   - Answer Construction (light blue)
   - LLM Formatting (green)
   - iOS App Display (blue)
2. **Arrows** between boxes with timing:
   - "1.2s retrieval"
   - "0.8s synthesis"
   - "1.5s generation"
3. **Content** inside each box:
   - Show actual query/response text
   - Use smaller font (14-16pt)
4. **Total time** (right side):
   - Large "3.5s" with stopwatch icon

**Colors**: Gradient from blue → green (top to bottom)

---

### SLIDE 13: Frontend Integration

**Visual Type**: API documentation with code

**How to Create**:
1. **Left**: API request
   - Code block (dark background)
   - JSON syntax highlighting
2. **Right**: API response
   - Code block (dark background)
   - JSON syntax highlighting
3. **Bottom**: Swift code snippet
   - Light gray background
   - Swift syntax highlighting

**Annotations**:
- Arrow pointing to endpoint URL
- Highlight key fields (answer, citations, confidence)

---

### SLIDE 14: Expected Frontend User Feedback

**Visual Type**: Dashboard with metrics

**How to Create**:
1. **4 quadrants**:
   - **Top-left**: Trust & Confidence
     - 4 metrics with percentages
     - Green checkmarks
   - **Top-right**: Usability
     - 4 metrics with percentages
     - Blue icons
   - **Bottom-left**: Response Quality
     - 4 metrics with ratings
     - Star icons
   - **Bottom-right**: Performance
     - 3 metrics
     - Speedometer icon

2. **Quotes** (bottom):
   - 3-4 user quotes in speech bubbles
   - Light blue background

---

### SLIDE 17: Retrieval Performance Analysis

**Visual Type**: Comparison table with winner highlight

**How to Create**:
1. **Table**: 4 rows × 4 columns
   - Headers: Metric | BM25 Only | Dense Only | Hybrid
   - Metrics: Recall, Precision, MRR, Latency
2. **Highlight**: "Hybrid" column
   - Green background
   - Bold text
   - Trophy icon in header
3. **Formula box** (bottom):
   - Show RRF formula
   - Light gray background

---

### SLIDE 21: Load Testing Results

**Visual Type**: Line graph with performance table

**How to Create**:
1. **Graph** (top):
   - X-axis: Concurrent users (10, 25, 50, 75, 100)
   - Y-axis: Response time (seconds)
   - 2 lines: Avg (blue), P95 (red)
   - Shaded area between lines
2. **Table** (bottom):
   - 5 rows (user counts)
   - 5 columns (metrics)
   - Color-code error rate (green <0.1%, amber <1%, red >1%)

**Annotations**:
- "Linear scaling" arrow (10-50 users)
- "Graceful degradation" arrow (50-100 users)

---

### SLIDE 23: Frontend Mobile UI Design

**Visual Type**: Mobile mockup

**How to Create**:
1. **Phone frame** (center):
   - iPhone outline (gray)
   - Screen content inside
2. **Screen content**:
   - Question box (top, light blue)
   - Answer text (middle, white)
   - Citations inline [1][2] (blue, clickable)
   - Sources section (bottom, expandable)
3. **Annotations** (outside phone):
   - Arrows pointing to features
   - Labels explaining interaction

**Use**: iPhone mockup template or draw custom

---

### SLIDE 24: A/B Testing Plan

**Visual Type**: Split comparison with metrics table

**How to Create**:
1. **Top**: Two columns
   - **Group A** (left): Control (no citations)
   - **Group B** (right): Treatment (with citations)
2. **Middle**: Metrics table
   - 6 rows (metrics)
   - 3 columns (Metric | Definition | Expected Impact)
   - Color-code expected impact (green for positive)
3. **Bottom**: Timeline
   - 5 weeks shown as horizontal bars
   - Week 1-2: Testing (blue)
   - Week 3: Analysis (amber)
   - Week 4: Decision (green)
   - Week 5+: Rollout (green)

---

### SLIDE 26: Summary - Key Takeaways

**Visual Type**: 5-column summary with icons

**How to Create**:
1. **5 columns**:
   - Architecture (🏗️)
   - Performance (⚡)
   - Testing (✅)
   - Production (🚀)
   - User Experience (⭐)
2. **Each column**:
   - Icon at top (large, 48pt)
   - 4-5 bullet points
   - Green checkmarks
3. **Bottom**: Large callout box
   - "The Bottom Line" in bold
   - Key message
   - Green background

---

## 🎯 Quick Tips

### For Tables
- Use alternating row colors (white/light gray)
- Bold headers
- Right-align numbers
- Left-align text

### For Code Blocks
- Dark background (#1E293B)
- Light text (#E2E8F0)
- Monospace font (Courier, Monaco, Consolas)
- Syntax highlighting (blue for keywords, green for strings)

### For Metrics
- Large numbers (32-48pt)
- Small labels (14-18pt)
- Use icons (✅ ❌ ⚡ 📊 🎯)
- Color-code (green=good, red=bad, amber=warning)

### For Diagrams
- Use consistent shapes (rectangles for processes, diamonds for decisions)
- Use arrows to show flow
- Label all connections
- Keep it simple (max 7 elements per diagram)

---

## 📦 Resources Needed

**Icons**: Download from:
- Heroicons (heroicons.com)
- Font Awesome (fontawesome.com)
- SF Symbols (for iOS mockups)

**Mockups**:
- iPhone mockup templates (Figma, Sketch)
- Cloud infrastructure icons (Google Cloud, AWS)

**Fonts**:
- Headers: Inter, SF Pro, Helvetica
- Body: Inter, SF Pro, Arial
- Code: Courier New, Monaco, Consolas

**Colors** (exact hex codes):
- Deep Blue: #1E3A8A
- Green: #10B981
- Cyan: #06B6D4
- Amber: #F59E0B
- Red: #EF4444
- Gray: #6B7280

---

**Total Visual Elements**: 26 slides with diagrams, charts, tables, and mockups  
**Estimated Design Time**: 4-6 hours (using templates)  
**Recommended Tool**: PowerPoint, Keynote, or Google Slides

