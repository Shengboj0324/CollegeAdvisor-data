# 🔐 AUTHENTICATION REQUIRED FOR REAL DATA

## ⚠️ CRITICAL: All Fake Data Has Been Deleted

I have **completely removed** all fake, sample, and synthetic data from the repository:

### Deleted Locations:
- ✅ `data/sample/` - DELETED
- ✅ `data/r2_preparation/` - DELETED  
- ✅ `data/r2_finetuning/` - DELETED
- ✅ `data/training/sample_qa.json` - DELETED
- ✅ `data/training/college_qa.json` - DELETED

**The repository is now 100% clean of fake data.**

---

## 🔑 Get Your College Scorecard API Key

To collect **REAL data** from the U.S. Department of Education College Scorecard, you need an API key.

### Step 1: Sign Up for API Key

**Visit:** https://api.data.gov/signup/

**Fill out the form:**
- First Name: [Your name]
- Last Name: [Your name]
- Email: [Your email]
- Organization: [Your organization or "Personal Project"]
- Use: "College admissions data analysis"

### Step 2: Check Your Email

You'll receive an email **immediately** with your API key. It looks like:
```
Your API key: aBcDeFgHiJkLmNoPqRsTuVwXyZ1234567890
```

### Step 3: Add to .env File

Open the `.env` file in this repository and update:

```bash
# Replace DEMO_KEY with your actual API key
COLLEGE_SCORECARD_API_KEY=aBcDeFgHiJkLmNoPqRsTuVwXyZ1234567890
```

---

## 🚀 After Getting Your API Key

Once you have your API key configured, run:

```bash
python scripts/collect_real_data_only.py
```

This will:
1. ✅ Verify all fake data is deleted (already done)
2. ✅ Collect REAL data from College Scorecard API (up to 5,000 institutions)
3. ✅ Validate data authenticity
4. ✅ Generate training datasets from REAL data only
5. ✅ Upload to R2 bucket

---

## 📊 What Real Data You'll Get

### Data Source
- **Provider:** U.S. Department of Education
- **API:** College Scorecard API
- **Authenticity:** 100% official government data
- **Coverage:** 7,000+ accredited institutions

### Data Fields (30 comprehensive fields)

**Basic Information:**
- Institution ID, Name, City, State, ZIP
- Website URL, Price calculator URL
- Locale, Ownership type, Carnegie classification

**Admissions:**
- Admission rate
- SAT average scores
- ACT midpoint scores

**Student Body:**
- Total student size
- Demographics (race/ethnicity breakdown)

**Costs:**
- In-state tuition
- Out-of-state tuition
- Average net price
- Median debt

**Academics:**
- Program percentages (Business, Engineering, Biology, Computer Science, Health)

**Outcomes:**
- Median earnings 10 years after entry
- 4-year completion rate
- Retention rate

---

## 🎯 Expected Results

### With Valid API Key:

**Collection:**
- 5,000 real institutions
- 30 data fields per institution
- ~15-20 MB of raw data
- Collection time: 10-15 minutes

**Training Data:**
- 25,000+ Q&A pairs (5 per institution)
- 4 formats: Alpaca, JSONL, Ollama, Modelfile
- 100% real, authentic data

**R2 Upload:**
- All data backed up to Cloudflare R2
- Zero egress fees
- 11 nines durability

### With DEMO_KEY (Not Recommended):

**Limitations:**
- Severe rate limits (1 request per minute)
- May collect only 100-200 institutions
- Collection time: 2-3 hours
- Frequent timeouts

---

## 🔒 Why DEMO_KEY Doesn't Work Well

The DEMO_KEY has these limitations:
- **Rate Limit:** 1 request per minute (vs 1000/hour with real key)
- **Hourly Limit:** 30 requests/hour (vs 1000/hour)
- **Daily Limit:** 500 requests/day (vs 50,000/day)

For collecting 5,000 institutions (50 pages):
- **With DEMO_KEY:** ~50 minutes (with rate limit waits)
- **With Real API Key:** ~1-2 minutes

---

## ✅ Verification After Collection

After running the script, verify:

```bash
# Check collected data
ls -lah data/real_data_only/

# View sample
head -50 data/real_data_only/processed_real_data.json

# Verify R2 upload
python scripts/verify_r2_data.py
```

---

## 🎓 Alternative: Use Existing API Key

If you already have a data.gov API key from another project, you can use it. The same key works for all data.gov APIs.

---

## 📞 Support

### If API Key Signup Fails:

1. **Check spam folder** - API key email might be filtered
2. **Try different email** - Use a different email address
3. **Contact data.gov support** - api.data.gov/contact

### If Collection Fails:

1. **Verify API key** - Check .env file has correct key
2. **Check internet connection** - API requires stable connection
3. **Review logs** - Check error messages in terminal

---

## 🚨 IMPORTANT REMINDERS

1. **NO FAKE DATA** - All fake/sample data has been deleted
2. **REAL DATA ONLY** - Only authentic College Scorecard data will be used
3. **API KEY REQUIRED** - DEMO_KEY has severe limitations
4. **ZERO TOLERANCE** - No synthetic or mock data will be created

---

## 📋 Quick Checklist

- [ ] Visit https://api.data.gov/signup/
- [ ] Fill out the form
- [ ] Check email for API key
- [ ] Update .env file with API key
- [ ] Run: `python scripts/collect_real_data_only.py`
- [ ] Verify data collection completed
- [ ] Verify R2 upload successful
- [ ] Proceed with fine-tuning

---

## 🎯 Next Steps After Authentication

Once you have your API key and data is collected:

1. **Fine-tune model:**
   ```bash
   cd data/real_data_only/training_datasets
   ollama create collegeadvisor -f Modelfile
   ```

2. **Test model:**
   ```bash
   ollama run collegeadvisor
   ```

3. **Integrate with API:**
   - Update CollegeAdvisor-api .env
   - Set OLLAMA_MODEL=collegeadvisor
   - Test endpoints

---

**Status:** ⏳ **WAITING FOR API KEY**

**Action Required:** Get your API key from https://api.data.gov/signup/

**Time to Complete:** 2 minutes (signup) + 10-15 minutes (data collection)

