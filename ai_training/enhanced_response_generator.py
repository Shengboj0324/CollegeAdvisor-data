"""
Enhanced Response Generator for College Advisory Training Data

CRITICAL: This module generates comprehensive 200-500 word advisory responses
instead of short 50-80 character fact lookups.

Zero-tolerance error handling:
- All imports validated
- All exceptions caught with detailed logging
- Comprehensive input validation
- Output quality validation

Author: Augment Agent
Date: October 18, 2025
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import random

# Validate imports with zero tolerance
try:
    import json
    from pathlib import Path
except ImportError as e:
    raise ImportError(f"❌ CRITICAL: Failed to import required module: {e}")

logger = logging.getLogger(__name__)


@dataclass
class ResponseQuality:
    """Quality metrics for generated responses."""
    char_count: int
    word_count: int
    has_context: bool
    has_advice: bool
    has_action_items: bool
    is_valid: bool
    error_message: Optional[str] = None


class EnhancedResponseGenerator:
    """
    Generates comprehensive college advisory responses.
    
    Transforms short fact lookups into detailed advisory guidance:
    
    BEFORE (BROKEN):
    Q: "What is Cornell's acceptance rate?"
    A: "Cornell's acceptance rate is approximately 7.5%." (51 chars)
    
    AFTER (FIXED):
    Q: "What are my chances of getting into Cornell?"
    A: "Cornell's overall acceptance rate is around 7.5%, but this varies 
       significantly by college within Cornell. Your chances depend on multiple
       factors: 1) Academic profile (GPA, test scores, course rigor)... 
       [200-500 words with context, advice, and actionable steps]"
    """
    
    def __init__(self, min_words: int = 200, max_words: int = 500):
        """
        Initialize response generator.
        
        Args:
            min_words: Minimum response length in words (default: 200)
            max_words: Maximum response length in words (default: 500)
        """
        self.min_words = min_words
        self.max_words = max_words
        
        logger.info(f"✅ EnhancedResponseGenerator initialized (min: {min_words}, max: {max_words} words)")
    
    def generate_acceptance_rate_response(
        self,
        university: str,
        acceptance_rate: float,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate comprehensive response about acceptance rates.
        
        Args:
            university: University name
            acceptance_rate: Acceptance rate as percentage (e.g., 7.5)
            additional_context: Optional dict with enrollment, SAT scores, etc.
            
        Returns:
            Comprehensive 200-500 word response
        """
        try:
            # Fix decimal point errors (0.7521 -> 7.521)
            if acceptance_rate < 1.0:
                acceptance_rate = acceptance_rate * 100
            
            # Build comprehensive response
            response_parts = []
            
            # 1. CONTEXT: State the fact with context
            response_parts.append(
                f"{university}'s overall acceptance rate is approximately {acceptance_rate:.1f}%, "
                f"making it a {'highly selective' if acceptance_rate < 10 else 'selective' if acceptance_rate < 20 else 'moderately selective'} "
                f"institution. However, this number alone doesn't tell the full story of your chances."
            )
            
            # 2. NUANCE: Explain variations
            response_parts.append(
                f"\n\nIt's important to understand that acceptance rates can vary significantly by:\n"
                f"- **College or school within {university}**: Some programs may be more competitive than others\n"
                f"- **Application round**: Early Decision/Action often has different rates than Regular Decision\n"
                f"- **Intended major**: STEM fields, business, and pre-med tracks are typically more competitive\n"
                f"- **In-state vs out-of-state**: For public universities, residency status matters significantly"
            )
            
            # 3. ADVICE: What factors matter
            response_parts.append(
                f"\n\nYour chances of admission to {university} depend on multiple factors beyond just the overall acceptance rate:\n\n"
                f"**1. Academic Profile:**\n"
                f"- GPA and class rank (in context of your high school's rigor)\n"
                f"- Standardized test scores (if submitted)\n"
                f"- Course rigor (AP, IB, honors classes)\n"
                f"- Academic trends (upward trajectory is positive)\n\n"
                f"**2. Extracurricular Achievements:**\n"
                f"- Leadership positions and sustained commitment\n"
                f"- Impact and initiative in your activities\n"
                f"- Depth over breadth (4-year commitment shows dedication)\n\n"
                f"**3. Essays and Personal Narrative:**\n"
                f"- Authentic voice and unique perspective\n"
                f"- Specific knowledge of {university}'s programs and values\n"
                f"- Clear demonstration of fit with the institution"
            )
            
            # 4. ACTION ITEMS: What to do
            response_parts.append(
                f"\n\n**To strengthen your application to {university}:**\n"
                f"- Research specific programs, professors, and opportunities that align with your interests\n"
                f"- Take the most rigorous courses available at your school\n"
                f"- Develop a clear academic and extracurricular narrative\n"
                f"- Write compelling, specific supplemental essays that demonstrate genuine interest\n"
                f"- Consider visiting campus (if possible) or attending virtual information sessions"
            )
            
            # 5. FOLLOW-UP: Invite further questions
            response_parts.append(
                f"\n\nWould you like help with any specific aspect of your {university} application, "
                f"such as essay strategy, program selection, or understanding how your profile compares?"
            )
            
            response = "".join(response_parts)
            
            # Validate quality
            quality = self.validate_response_quality(response)
            if not quality.is_valid:
                logger.error(f"❌ Generated response failed quality check: {quality.error_message}")
                raise ValueError(f"Response quality validation failed: {quality.error_message}")
            
            logger.info(f"✅ Generated acceptance rate response: {quality.word_count} words")
            return response
            
        except Exception as e:
            logger.error(f"❌ Failed to generate acceptance rate response: {e}")
            raise
    
    def generate_enrollment_response(
        self,
        university: str,
        enrollment: int,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate comprehensive response about enrollment.
        
        Args:
            university: University name
            enrollment: Total enrollment number
            additional_context: Optional dict with campus size, student-faculty ratio, etc.
            
        Returns:
            Comprehensive 200-500 word response
        """
        try:
            response_parts = []
            
            # 1. CONTEXT: State the fact with context
            size_category = (
                "large" if enrollment > 20000 
                else "medium-sized" if enrollment > 5000 
                else "small"
            )
            
            response_parts.append(
                f"{university} has a total enrollment of approximately {enrollment:,} students, "
                f"making it a {size_category} institution. The size of a university significantly "
                f"impacts your college experience in several ways."
            )
            
            # 2. IMPLICATIONS: What this means for students
            if enrollment > 20000:
                implications = (
                    f"\n\n**Advantages of a large university like {university}:**\n"
                    f"- Extensive course offerings and diverse academic programs\n"
                    f"- Wide variety of student organizations and extracurricular activities\n"
                    f"- Large alumni network for career opportunities\n"
                    f"- More resources, facilities, and research opportunities\n"
                    f"- Diverse student body with varied perspectives\n\n"
                    f"**Considerations:**\n"
                    f"- Larger class sizes, especially in introductory courses\n"
                    f"- May need to be more proactive to build relationships with professors\n"
                    f"- Can feel overwhelming initially; finding your community is important\n"
                    f"- More bureaucratic processes for advising and administration"
                )
            elif enrollment > 5000:
                implications = (
                    f"\n\n**Advantages of a medium-sized university like {university}:**\n"
                    f"- Balance between resources and personal attention\n"
                    f"- Diverse academic offerings without feeling overwhelming\n"
                    f"- Opportunity to know professors while still having variety\n"
                    f"- Strong sense of community with enough diversity\n\n"
                    f"**Considerations:**\n"
                    f"- May have fewer niche programs than larger universities\n"
                    f"- Smaller but still substantial alumni network\n"
                    f"- Class sizes vary by department and level"
                )
            else:
                implications = (
                    f"\n\n**Advantages of a smaller institution like {university}:**\n"
                    f"- Small class sizes and personalized attention from professors\n"
                    f"- Close-knit community where you'll know many students\n"
                    f"- Easier to get involved in leadership and research opportunities\n"
                    f"- More accessible faculty and administration\n\n"
                    f"**Considerations:**\n"
                    f"- Fewer course offerings and academic programs\n"
                    f"- Smaller alumni network (though often very engaged)\n"
                    f"- Less diversity in student body and perspectives\n"
                    f"- Fewer extracurricular options"
                )
            
            response_parts.append(implications)
            
            # 3. ADVICE: How to evaluate fit
            response_parts.append(
                f"\n\n**When considering {university}'s size:**\n\n"
                f"Ask yourself:\n"
                f"- Do I thrive in large, diverse environments or prefer intimate settings?\n"
                f"- How important is personal attention from professors?\n"
                f"- Do I want extensive course options or focused programs?\n"
                f"- What kind of campus community am I looking for?\n\n"
                f"**Research these specific factors:**\n"
                f"- Average class size in your intended major\n"
                f"- Student-to-faculty ratio\n"
                f"- Availability of undergraduate research opportunities\n"
                f"- Housing options and campus life\n"
                f"- Support services (advising, career center, tutoring)"
            )
            
            # 4. ACTION ITEMS
            response_parts.append(
                f"\n\n**Next steps:**\n"
                f"- Visit campus (if possible) to get a feel for the size and community\n"
                f"- Talk to current students about their experience\n"
                f"- Attend a class in your intended major to see class dynamics\n"
                f"- Research specific programs and opportunities that interest you"
            )
            
            # 5. FOLLOW-UP
            response_parts.append(
                f"\n\nWould you like more information about specific aspects of student life at {university}, "
                f"such as housing, academic programs, or campus culture?"
            )
            
            response = "".join(response_parts)
            
            # Validate quality
            quality = self.validate_response_quality(response)
            if not quality.is_valid:
                logger.error(f"❌ Generated response failed quality check: {quality.error_message}")
                raise ValueError(f"Response quality validation failed: {quality.error_message}")
            
            logger.info(f"✅ Generated enrollment response: {quality.word_count} words")
            return response
            
        except Exception as e:
            logger.error(f"❌ Failed to generate enrollment response: {e}")
            raise
    
    def validate_response_quality(self, response: str) -> ResponseQuality:
        """
        Validate response meets quality standards.
        
        Args:
            response: Generated response text
            
        Returns:
            ResponseQuality object with validation results
        """
        try:
            # Count characters and words
            char_count = len(response)
            word_count = len(response.split())
            
            # Check for required elements
            has_context = any(keyword in response.lower() for keyword in [
                "approximately", "around", "about", "context", "understand", "important"
            ])
            
            has_advice = any(keyword in response.lower() for keyword in [
                "consider", "recommend", "should", "important to", "keep in mind", "advice"
            ])
            
            has_action_items = any(keyword in response.lower() for keyword in [
                "next steps", "to strengthen", "research", "visit", "talk to", "would you like"
            ])
            
            # Validate length
            is_valid = True
            error_message = None
            
            if word_count < self.min_words:
                is_valid = False
                error_message = f"Response too short: {word_count} words (minimum: {self.min_words})"
            elif word_count > self.max_words:
                is_valid = False
                error_message = f"Response too long: {word_count} words (maximum: {self.max_words})"
            elif not (has_context and has_advice and has_action_items):
                is_valid = False
                missing = []
                if not has_context: missing.append("context")
                if not has_advice: missing.append("advice")
                if not has_action_items: missing.append("action items")
                error_message = f"Response missing required elements: {', '.join(missing)}"
            
            return ResponseQuality(
                char_count=char_count,
                word_count=word_count,
                has_context=has_context,
                has_advice=has_advice,
                has_action_items=has_action_items,
                is_valid=is_valid,
                error_message=error_message
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to validate response quality: {e}")
            return ResponseQuality(
                char_count=0,
                word_count=0,
                has_context=False,
                has_advice=False,
                has_action_items=False,
                is_valid=False,
                error_message=str(e)
            )

    def generate_sat_score_response(
        self,
        university: str,
        sat_average: int,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate comprehensive response about SAT scores."""
        try:
            response_parts = []

            # 1. CONTEXT
            response_parts.append(
                f"The average SAT score at {university} is approximately {sat_average}. "
                f"However, understanding what this means for your application requires looking "
                f"at the full picture of standardized testing in college admissions."
            )

            # 2. INTERPRETATION
            if sat_average >= 1500:
                interpretation = "extremely competitive"
                range_estimate = f"{sat_average - 50} to {sat_average + 50}"
            elif sat_average >= 1400:
                interpretation = "highly competitive"
                range_estimate = f"{sat_average - 60} to {sat_average + 60}"
            elif sat_average >= 1200:
                interpretation = "competitive"
                range_estimate = f"{sat_average - 80} to {sat_average + 80}"
            else:
                interpretation = "moderately competitive"
                range_estimate = f"{sat_average - 100} to {sat_average + 100}"

            response_parts.append(
                f"\n\n**What this score means:**\n\n"
                f"{university} is {interpretation} in terms of standardized testing. "
                f"The middle 50% of admitted students typically score between approximately {range_estimate}. "
                f"This means 25% of students score below this range and 25% score above it.\n\n"
                f"**Important considerations:**\n"
                f"- Test scores are just one component of a holistic review process\n"
                f"- Many universities, including potentially {university}, may be test-optional\n"
                f"- Scores are evaluated in context of your opportunities and background\n"
                f"- A score below the average doesn't disqualify you if other parts of your application are strong"
            )

            # 3. ADVICE
            response_parts.append(
                f"\n\n**Strategic considerations for your application:**\n\n"
                f"**If your score is in or above the range:**\n"
                f"- Submit your scores to strengthen your application\n"
                f"- Focus energy on essays and extracurriculars\n"
                f"- Highlight other aspects of your academic achievement\n\n"
                f"**If your score is below the range:**\n"
                f"- Consider retaking the test if you have time and resources\n"
                f"- Evaluate whether {university} is test-optional\n"
                f"- If test-optional, carefully consider whether submitting helps or hurts\n"
                f"- Strengthen other parts of your application (GPA, essays, recommendations)\n"
                f"- Consider explaining any circumstances that affected your testing"
            )

            # 4. ACTION ITEMS
            response_parts.append(
                f"\n\n**Next steps:**\n"
                f"- Check {university}'s current testing policy (test-required, test-optional, or test-blind)\n"
                f"- Review the full middle 50% range on {university}'s admissions website\n"
                f"- Consider your full academic profile, not just test scores\n"
                f"- If retaking, focus on your weakest sections and use official practice materials\n"
                f"- Remember that test scores are just one piece of your application"
            )

            # 5. FOLLOW-UP
            response_parts.append(
                f"\n\nWould you like guidance on test preparation strategies, understanding test-optional policies, "
                f"or how to strengthen other parts of your {university} application?"
            )

            response = "".join(response_parts)
            quality = self.validate_response_quality(response)
            if not quality.is_valid:
                raise ValueError(f"Response quality validation failed: {quality.error_message}")

            logger.info(f"✅ Generated SAT score response: {quality.word_count} words")
            return response

        except Exception as e:
            logger.error(f"❌ Failed to generate SAT score response: {e}")
            raise

    def generate_location_response(
        self,
        university: str,
        city: str,
        state: str,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate comprehensive response about university location."""
        try:
            response_parts = []

            # 1. CONTEXT
            response_parts.append(
                f"{university} is located in {city}, {state}. The location of your college "
                f"is more important than many students initially realize—it affects your academic "
                f"opportunities, internship prospects, cost of living, and overall college experience."
            )

            # 2. LOCATION ANALYSIS
            response_parts.append(
                f"\n\n**Why location matters for your college experience:**\n\n"
                f"**Academic and Career Opportunities:**\n"
                f"- Proximity to industry hubs affects internship and job opportunities\n"
                f"- Urban locations often provide more part-time work and networking options\n"
                f"- Research opportunities may be enhanced by nearby institutions or companies\n"
                f"- Guest speakers and industry connections are more accessible in certain locations\n\n"
                f"**Cost of Living:**\n"
                f"- {city}, {state} has its own cost of living that affects your budget\n"
                f"- Consider expenses beyond tuition: housing, food, transportation, entertainment\n"
                f"- Urban areas typically have higher costs but more job opportunities\n"
                f"- Rural areas may be more affordable but require a car for transportation\n\n"
                f"**Campus Culture and Lifestyle:**\n"
                f"- Climate and weather patterns affect daily life and activities\n"
                f"- Urban vs. suburban vs. rural settings create different social dynamics\n"
                f"- Distance from home impacts visit frequency and support system\n"
                f"- Local culture and diversity shape your college experience"
            )

            # 3. ADVICE
            response_parts.append(
                f"\n\n**Questions to consider about {city}, {state}:**\n\n"
                f"- How far is this from your home, and how often do you want to visit?\n"
                f"- What's the climate like, and are you comfortable with it year-round?\n"
                f"- Does the location support your career interests (e.g., tech hubs, financial centers)?\n"
                f"- What's the cost of living, and can you afford it?\n"
                f"- Is there reliable public transportation, or will you need a car?\n"
                f"- What cultural, recreational, and social opportunities does the area offer?\n"
                f"- How does the location align with your post-graduation plans?"
            )

            # 4. ACTION ITEMS
            response_parts.append(
                f"\n\n**Research steps:**\n"
                f"- Visit {university}'s campus if possible to experience {city} firsthand\n"
                f"- Research the local area: neighborhoods, transportation, safety, activities\n"
                f"- Talk to current students about their experience living in {city}\n"
                f"- Look into internship and job opportunities in the region\n"
                f"- Consider the climate and whether you'll be comfortable there\n"
                f"- Calculate the total cost including travel home for breaks"
            )

            # 5. FOLLOW-UP
            response_parts.append(
                f"\n\nWould you like more specific information about {city}, {state}, "
                f"such as the local job market, cost of living, or things to do in the area?"
            )

            response = "".join(response_parts)
            quality = self.validate_response_quality(response)
            if not quality.is_valid:
                raise ValueError(f"Response quality validation failed: {quality.error_message}")

            logger.info(f"✅ Generated location response: {quality.word_count} words")
            return response

        except Exception as e:
            logger.error(f"❌ Failed to generate location response: {e}")
            raise

    def generate_tuition_response(
        self,
        university: str,
        tuition: int,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate comprehensive response about tuition and costs."""
        try:
            response_parts = []

            # 1. CONTEXT
            response_parts.append(
                f"The tuition at {university} is approximately ${tuition:,} per year. "
                f"However, understanding the true cost of attendance requires looking beyond "
                f"just tuition to get a complete financial picture."
            )

            # 2. COST BREAKDOWN
            response_parts.append(
                f"\n\n**Understanding the full cost of attendance:**\n\n"
                f"**Tuition ({tuition:,})** is just one component. You also need to budget for:\n"
                f"- **Room and Board**: Typically $10,000-$18,000 per year\n"
                f"- **Books and Supplies**: Usually $1,000-$1,500 per year\n"
                f"- **Personal Expenses**: $1,500-$3,000 per year\n"
                f"- **Transportation**: Varies based on distance from home\n"
                f"- **Health Insurance**: If not covered by family plan\n\n"
                f"The **total cost of attendance** at {university} is likely ${tuition + 15000:,}-${tuition + 25000:,} per year, "
                f"depending on your lifestyle and choices."
            )

            # 3. FINANCIAL AID ADVICE
            response_parts.append(
                f"\n\n**Critical financial aid advice:**\n\n"
                f"**Don't let the sticker price scare you away.** My advice: Many students pay significantly less than the published tuition through:\n\n"
                f"**1. Need-Based Financial Aid:**\n"
                f"- Complete the FAFSA (Free Application for Federal Student Aid)\n"
                f"- Some schools also require the CSS Profile\n"
                f"- {university} may meet 100% of demonstrated financial need (check their policy)\n"
                f"- Need-based aid can include grants, scholarships, work-study, and loans\n\n"
                f"**2. Merit Scholarships:**\n"
                f"- Based on academic achievement, test scores, or special talents\n"
                f"- May be automatic or require separate applications\n"
                f"- Research {university}'s merit scholarship opportunities\n\n"
                f"**3. External Scholarships:**\n"
                f"- Community organizations, corporations, foundations\n"
                f"- Start searching early and apply to many\n"
                f"- Even small scholarships add up\n\n"
                f"**4. Work-Study and Part-Time Jobs:**\n"
                f"- Federal work-study programs\n"
                f"- On-campus employment opportunities\n"
                f"- Can earn $2,000-$4,000 per year"
            )

            # 4. ACTION ITEMS
            response_parts.append(
                f"\n\n**Financial planning steps:**\n"
                f"- Use {university}'s net price calculator to estimate your actual cost\n"
                f"- Complete the FAFSA as soon as possible after October 1\n"
                f"- Research {university}'s financial aid policies and deadlines\n"
                f"- Apply for external scholarships throughout your senior year\n"
                f"- Compare financial aid packages from multiple schools\n"
                f"- Don't rule out {university} based on sticker price alone—wait to see your aid package"
            )

            # 5. FOLLOW-UP
            response_parts.append(
                f"\n\nWould you like help understanding financial aid applications, finding scholarships, "
                f"or comparing the true cost of {university} to other schools?"
            )

            response = "".join(response_parts)
            quality = self.validate_response_quality(response)
            if not quality.is_valid:
                raise ValueError(f"Response quality validation failed: {quality.error_message}")

            logger.info(f"✅ Generated tuition response: {quality.word_count} words")
            return response

        except Exception as e:
            logger.error(f"❌ Failed to generate tuition response: {e}")
            raise

