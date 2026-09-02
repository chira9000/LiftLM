"""Curated strength-training knowledge base.

Each entry is a short, evidence-grounded summary of a core training-science
topic, bundled with real PubMed citations (verified PMIDs) so the coach can
ground its advice instead of relying on the LLM's own (unverifiable) recall.
This static set is the offline fallback; `app.services.knowledge.pubmed`
supplements it with a live PubMed search at request time when enabled.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PubMedCitation:
    pmid: str
    citation: str  # "Author et al. (Year). Title."

    @property
    def url(self) -> str:
        return f"https://pubmed.ncbi.nlm.nih.gov/{self.pmid}/"

    def to_dict(self) -> dict:
        return {"pmid": self.pmid, "citation": self.citation, "url": self.url}


@dataclass(frozen=True)
class KnowledgeEntry:
    topic: str  # canonical slug used for retrieval
    title: str
    keywords: list[str]
    summary: str
    key_points: list[str]
    citations: list[PubMedCitation] = field(default_factory=list)
    # Precise NCBI query for live PubMed lookups. Loose queries like a bare
    # title ("Common Plateaus") let PubMed's term-mapping drift into
    # unrelated fields (biotech, food science, etc.) — [tiab] plus an
    # explicit resistance-training/strength anchor keeps live results on topic.
    pubmed_query: str = ""

    def to_dict(self) -> dict:
        return {
            "topic": self.topic,
            "title": self.title,
            "summary": self.summary,
            "key_points": self.key_points,
            "citations": [c.to_dict() for c in self.citations],
        }


KNOWLEDGE_BASE: list[KnowledgeEntry] = [
    KnowledgeEntry(
        topic="exercise_information",
        title="Exercise Selection",
        pubmed_query='("resistance training"[tiab] OR "strength training"[tiab]) AND "exercise selection"[tiab]',
        keywords=[
            "exercise selection", "compound", "isolation", "which exercise",
            "free weight", "machine", "barbell vs dumbbell", "variation",
        ],
        summary=(
            "Compound (multi-joint) lifts drive the majority of strength and "
            "hypertrophy adaptation; isolation exercises are best used to "
            "target a lagging muscle or add volume without extra systemic fatigue."
        ),
        key_points=[
            "Compound lifts (squat, bench, deadlift, row, press) recruit the most muscle mass per set and should anchor most programs.",
            "Isolation exercises add targeted volume to a muscle group with lower fatigue cost per set.",
            "Free weights train stabilizer muscles and balance; machines let you push closer to failure safely and reduce technical skill demands.",
            "Exercise choice matters less than progressive overload applied consistently to whichever exercises you pick.",
        ],
        citations=[
            PubMedCitation("41843416", "Currier et al. (2026). ACSM Position Stand: Resistance Training Prescription for Muscle Function, Hypertrophy, and Physical Performance in Healthy Adults."),
            PubMedCitation("37414459", "Currier et al. (2023). Resistance training prescription for muscle strength and hypertrophy in healthy adults: a systematic review and Bayesian network meta-analysis."),
        ],
    ),
    KnowledgeEntry(
        topic="training_principles",
        title="Training Principles",
        pubmed_query='"resistance training"[tiab] AND ("training principles"[tiab] OR specificity[tiab])',
        keywords=[
            "training principle", "principles of training", "specificity",
            "overload principle", "individual variation", "adaptation",
        ],
        summary=(
            "Strength training adaptation is governed by a small set of "
            "principles: specificity (train what you want to improve), "
            "progressive overload, and individual variation in response."
        ),
        key_points=[
            "Specificity: adaptations are specific to the stimulus — train the rep ranges/movements that match your goal.",
            "Progressive overload is the primary long-term driver of continued strength and muscle gain.",
            "Fatigue management (recovery, volume, intensity balance) determines how much of that overload can actually be realized as adaptation.",
            "Individual response varies significantly — use your own trend data, not just population averages, to guide adjustments.",
        ],
        citations=[
            PubMedCitation("41843416", "Currier et al. (2026). ACSM Position Stand: Resistance Training Prescription for Muscle Function, Hypertrophy, and Physical Performance in Healthy Adults."),
            PubMedCitation("38286426", "Chaves et al. (2024). Effects of Resistance Training Overload Progression Protocols on Strength and Muscle Mass."),
        ],
    ),
    KnowledgeEntry(
        topic="progressive_overload",
        title="Progressive Overload",
        pubmed_query='"progressive overload"[tiab] AND "resistance training"[tiab]',
        keywords=[
            "progressive overload", "overload", "progression", "increase weight",
            "add weight", "get stronger",
        ],
        summary=(
            "Progressive overload — gradually increasing weight, reps, sets, or "
            "difficulty over time — is the primary mechanism driving continued "
            "strength and hypertrophy gains once initial adaptation plateaus."
        ),
        key_points=[
            "Overload can be applied via load, reps, sets, density (rest reduction), or range of motion — not just adding weight.",
            "Small, consistent increases (e.g. +2.5–5 lbs or +1 rep) outperform large, sporadic jumps for long-term progress.",
            "Training with sufficient proximity to failure is necessary for overload to translate into adaptation, especially for hypertrophy.",
            "Progress is not linear — expect short plateaus and use trend data across weeks, not single sessions, to judge progression.",
        ],
        citations=[
            PubMedCitation("38286426", "Chaves et al. (2024). Effects of Resistance Training Overload Progression Protocols on Strength and Muscle Mass."),
            PubMedCitation("37144554", "Ruple et al. (2023). The effects of resistance training to near failure on strength, hypertrophy, and motor unit adaptations in previously trained adults."),
            PubMedCitation("41843416", "Currier et al. (2026). ACSM Position Stand: Resistance Training Prescription for Muscle Function, Hypertrophy, and Physical Performance in Healthy Adults."),
        ],
    ),
    KnowledgeEntry(
        topic="volume",
        title="Training Volume",
        pubmed_query='"resistance training"[tiab] AND "training volume"[tiab] AND (hypertrophy[tiab] OR strength[tiab])',
        keywords=[
            "volume", "sets per week", "how many sets", "weekly sets", "set volume",
        ],
        summary=(
            "Weekly hard sets per muscle group show a dose-response relationship "
            "with hypertrophy up to a point, after which returns diminish and "
            "recovery becomes the limiting factor."
        ),
        key_points=[
            "Roughly 10–20 hard sets per muscle group per week is a common evidence-based range for hypertrophy in trained lifters; beginners need less.",
            "More volume generally means more growth up to an individual recoverable ceiling — beyond that, added volume just adds fatigue.",
            "Volume and frequency trade off: the same weekly volume split across 2 sessions/week tends to outperform 1 session/week for a muscle group.",
            "Track weekly volume trend (not single-session totals) to judge whether you're overreaching or under-training.",
        ],
        citations=[
            PubMedCitation("27433992", "Schoenfeld et al. (2017). Dose-response relationship between weekly resistance training volume and increases in muscle mass: A systematic review and meta-analysis."),
            PubMedCitation("41343037", "Pelland et al. (2026). The Resistance Training Dose Response: Meta-Regressions Exploring the Effects of Weekly Volume and Frequency on Muscle Hypertrophy and Strength Gains."),
            PubMedCitation("27102172", "Schoenfeld et al. (2016). Effects of Resistance Training Frequency on Measures of Muscle Hypertrophy: A Systematic Review and Meta-Analysis."),
        ],
    ),
    KnowledgeEntry(
        topic="intensity",
        title="Training Intensity",
        pubmed_query='"resistance training"[tiab] AND (intensity[tiab] OR "1RM"[tiab]) AND (strength[tiab] OR hypertrophy[tiab])',
        keywords=[
            "intensity", "percent 1rm", "%1rm", "how heavy", "load selection",
        ],
        summary=(
            "Intensity (load relative to 1RM) shapes the strength/hypertrophy "
            "balance of a program, but a wide range of loads can build muscle "
            "if training is taken close enough to failure."
        ),
        key_points=[
            "Heavy loads (>80% 1RM, ~1–6 reps) are most efficient for maximal strength and neural adaptation.",
            "Moderate loads (~65–80% 1RM, ~6–15 reps) are effective for hypertrophy and are easier to recover from across high volume.",
            "Light loads can still build muscle comparably to heavy loads when sets are taken close to failure, though strength gains favor heavier loads.",
            "Intensity and proximity to failure both matter — a heavy set stopped far from failure provides less stimulus than expected.",
        ],
        citations=[
            PubMedCitation("38970765", "Robinson et al. (2024). Exploring the Dose-Response Relationship Between Estimated Resistance Training Proximity to Failure, Strength Gain, and Muscle Hypertrophy: A Series of Meta-Regressions."),
            PubMedCitation("37414459", "Currier et al. (2023). Resistance training prescription for muscle strength and hypertrophy in healthy adults: a systematic review and Bayesian network meta-analysis."),
        ],
    ),
    KnowledgeEntry(
        topic="rpe_rir",
        title="RPE / RIR (Autoregulation)",
        pubmed_query='("rating of perceived exertion"[tiab] OR "repetitions in reserve"[tiab]) AND "resistance training"[tiab]',
        keywords=[
            "rpe", "rir", "reps in reserve", "perceived exertion", "autoregulation",
            "how hard", "how heavy should i go",
        ],
        summary=(
            "RPE (Rating of Perceived Exertion) and RIR (Reps in Reserve) let "
            "lifters autoregulate load session-to-session based on how a set "
            "actually feels, and are reasonably valid proxies for proximity to failure."
        ),
        key_points=[
            "RIR estimates how many more reps you could have done; RPE 10 = failure, RPE 8 ≈ 2 RIR, RPE 7 ≈ 3 RIR.",
            "A working sweet spot for most goals is RPE 7–9 (1–3 RIR) — hard enough to drive adaptation without excessive fatigue every session.",
            "RPE/RIR accuracy improves with training experience; beginners tend to underestimate how many reps they have left.",
            "Chronically training at RPE 9–10 every set raises fatigue and injury risk without proportionally more gains than RPE 7–8.5.",
        ],
        citations=[
            PubMedCitation("38910451", "Petro et al. (2025). Validity of Rating of Perceived Exertion Scales in Relation to Movement Velocity and Exercise Intensity During Resistance-Exercise: A Systematic Review."),
            PubMedCitation("40902458", "Gómez-Redondo et al. (2025). Validity of repetitions in reserve for prescribing resistance exercise in older adults."),
        ],
    ),
    KnowledgeEntry(
        topic="recovery",
        title="Recovery",
        pubmed_query='(sleep[tiab] OR recovery[tiab]) AND "resistance training"[tiab] AND (strength[tiab] OR performance[tiab])',
        keywords=[
            "recovery", "rest day", "sleep", "sore", "soreness", "doms",
            "overtrained", "overtraining", "fatigue",
        ],
        summary=(
            "Recovery — sleep, rest between sessions, and total stress load — "
            "determines how much of your training volume actually converts to "
            "adaptation rather than accumulated fatigue."
        ),
        key_points=[
            "Sleep is one of the most impactful and controllable recovery levers for strength, power, and hypertrophy outcomes.",
            "Muscle soreness (DOMS) is not a reliable indicator of workout quality and typically fades within 48–72 hours with training experience.",
            "At least 48 hours between hard sessions for the same muscle group is a reasonable default to allow recovery.",
            "Persistent underperformance, elevated resting heart rate, or mood disturbance across weeks can signal overtraining — a deload or reduced volume week is the standard fix.",
        ],
        citations=[
            PubMedCitation("31288293", "Vitale et al. (2019). Sleep Hygiene for Optimizing Recovery in Athletes: Review and Recommendations."),
            PubMedCitation("25645125", "Thun et al. (2015). Sleep, circadian rhythms, and athletic performance."),
        ],
    ),
    KnowledgeEntry(
        topic="programming",
        title="Programming",
        pubmed_query='"resistance training"[tiab] AND (periodization[tiab] OR "program design"[tiab])',
        keywords=[
            "programming", "program design", "periodization", "mesocycle",
            "training split", "program structure",
        ],
        summary=(
            "Programming is how volume, intensity, and exercise selection are "
            "organized over weeks and months — periodized structure generally "
            "outperforms static, unchanging programs for long-term progress."
        ),
        key_points=[
            "Both linear and undulating periodization models outperform doing the same sets/reps/load indefinitely for strength and hypertrophy.",
            "Split choice (full-body, upper/lower, push/pull/legs) matters less than hitting adequate weekly volume and frequency per muscle group.",
            "Programs should progress systematically (see progressive overload) and include planned lower-stress weeks (see deloading).",
            "Program adherence is often a bigger predictor of results than which specific evidence-based template is used.",
        ],
        citations=[
            PubMedCitation("41843416", "Currier et al. (2026). ACSM Position Stand: Resistance Training Prescription for Muscle Function, Hypertrophy, and Physical Performance in Healthy Adults."),
            PubMedCitation("37414459", "Currier et al. (2023). Resistance training prescription for muscle strength and hypertrophy in healthy adults: a systematic review and Bayesian network meta-analysis."),
        ],
    ),
    KnowledgeEntry(
        topic="deloading",
        title="Deloading",
        pubmed_query='(taper[tiab] OR tapering[tiab] OR deload[tiab]) AND (strength[tiab] OR performance[tiab] OR training[tiab])',
        keywords=[
            "deload", "deloading", "taper", "tapering", "reduce volume", "back off week",
        ],
        summary=(
            "A deload is a planned, short reduction in training volume and/or "
            "intensity used to dissipate accumulated fatigue before it becomes "
            "overtraining, without losing meaningful fitness."
        ),
        key_points=[
            "A common deload cuts volume by ~40–60% for 5–10 days while keeping some intensity, to preserve neuromuscular adaptation.",
            "Tapering (a deload before competition/testing) reliably improves performance by shedding fatigue while retaining fitness.",
            "Deloads are typically scheduled every 4–8 weeks of hard training, or triggered reactively when performance stalls or soreness/fatigue accumulates.",
            "A properly timed deload should not cause detraining — strength is usually maintained or slightly improved afterward.",
        ],
        citations=[
            PubMedCitation("42611173", "Winwood et al. (2026). Tapering and Peaking in the Weight Lifting Sports: A Systematic Review of Athletes' Self-Reported Strategies."),
            PubMedCitation("32172680", "Vachon et al. (2021). Effects of tapering on neuromuscular and metabolic fitness in team sports: a systematic review and meta-analysis."),
        ],
    ),
    KnowledgeEntry(
        topic="technique",
        title="Technique & Injury Prevention",
        pubmed_query='("resistance training"[tiab] OR weightlifting[tiab] OR powerlifting[tiab]) AND (injury[tiab] OR technique[tiab])',
        keywords=[
            "technique", "form", "injury", "hurt", "safe", "safety", "proper form",
        ],
        summary=(
            "Consistent technique under load is what makes progressive overload "
            "safe and repeatable; most resistance-training injuries relate to "
            "rapid load/volume spikes rather than a single exercise being unsafe."
        ),
        key_points=[
            "Injury rates in weightlifting/powerlifting are lower than most team sports, and most injuries are overuse-related, not acute-form failures.",
            "Sudden increases in training load or volume are a leading modifiable risk factor for injury — this is why progressive overload should be gradual.",
            "Technique should be grooved at submaximal loads before pushing intensity — video review against known form cues catches most breakdowns.",
            "Supervised, well-programmed resistance training is safe and beneficial across age groups, including youth and older adults.",
        ],
        citations=[
            PubMedCitation("27707741", "Aasa et al. (2017). Injuries among weightlifters and powerlifters: a systematic review."),
            PubMedCitation("33322981", "Ángel Rodríguez et al. (2022). Injury in CrossFit®: A Systematic Review of Epidemiology and Risk Factors."),
            PubMedCitation("19945973", "Faigenbaum et al. (2010). Resistance training among young athletes: safety, efficacy and injury prevention effects."),
        ],
    ),
    KnowledgeEntry(
        topic="plateaus",
        title="Common Plateaus",
        pubmed_query='"resistance training"[tiab] AND (plateau[tiab] OR "proximity to failure"[tiab] OR "training stagnation"[tiab])',
        keywords=[
            "plateau", "plateaued", "stuck", "stalled", "stalling", "not progressing",
            "no progress", "flatlined",
        ],
        summary=(
            "Plateaus usually stem from insufficient progressive overload, "
            "inadequate recovery, or volume/intensity that has drifted outside "
            "the effective range — rarely from the exercise itself."
        ),
        key_points=[
            "Check proximity to failure first: sets consistently left several reps in the tank under-stimulate adaptation (see RPE/RIR).",
            "Check frequency and volume trend: a lift trained under 1–1.5x/week or with declining weekly volume commonly stalls.",
            "Check recovery: poor sleep, high life stress, or insufficient calories/protein blunt strength progress even with a good program.",
            "A deload followed by a fresh progression block is a standard, evidence-backed reset for a genuine plateau.",
        ],
        citations=[
            PubMedCitation("37144554", "Ruple et al. (2023). The effects of resistance training to near failure on strength, hypertrophy, and motor unit adaptations in previously trained adults."),
            PubMedCitation("38970765", "Robinson et al. (2024). Exploring the Dose-Response Relationship Between Estimated Resistance Training Proximity to Failure, Strength Gain, and Muscle Hypertrophy: A Series of Meta-Regressions."),
            PubMedCitation("27433992", "Schoenfeld et al. (2017). Dose-response relationship between weekly resistance training volume and increases in muscle mass: A systematic review and meta-analysis."),
        ],
    ),
    KnowledgeEntry(
        topic="strength_standards",
        title="Strength Standards",
        pubmed_query='(powerlifting[tiab] OR "muscular strength"[tiab]) AND (normative[tiab] OR "reference values"[tiab] OR performance[tiab])',
        keywords=[
            "strength standard", "how strong", "am i strong", "average lift",
            "beginner intermediate advanced", "good bench", "good squat", "good deadlift",
        ],
        summary=(
            "Strength standards (bodyweight-relative benchmarks for squat/bench/"
            "deadlift) are mostly derived from competition and normative-testing "
            "data rather than randomized trials — useful as rough orientation, "
            "not a precise target."
        ),
        key_points=[
            "Competition totals from powerlifting federations are the most reliable empirical source for lift-specific bodyweight-relative standards.",
            "Normative strength testing (e.g. grip strength) confirms strength varies substantially by age, sex, and training history — treat standards as wide bands, not fixed lines.",
            "Standards are most useful for tracking your own trajectory (novice → intermediate → advanced) rather than comparing directly to others.",
            "Rate of progress naturally slows as you approach your genetic/training-age ceiling — this is expected, not a sign something is wrong.",
        ],
        citations=[
            PubMedCitation("30844981", "Ferland et al. (2019). Classic Powerlifting Performance: A Systematic Review."),
            PubMedCitation("39647778", "Tomkinson et al. (2025). International norms for adult handgrip strength: A systematic review of data on 2.4 million adults aged 20 to 100+ years from 69 countries and regions."),
        ],
    ),
    KnowledgeEntry(
        topic="nutrition_basics",
        title="Nutrition Basics",
        pubmed_query='"dietary protein"[tiab] AND "resistance training"[tiab] AND (hypertrophy[tiab] OR "muscle mass"[tiab])',
        keywords=[
            "nutrition", "protein", "diet", "calories", "eat", "eating", "bulk",
            "cut", "cutting", "bulking", "macros",
        ],
        summary=(
            "Total protein intake and overall energy balance matter far more "
            "for strength/hypertrophy outcomes than meal timing or micro-optimized macros."
        ),
        key_points=[
            "~1.6–2.2 g/kg bodyweight/day of protein is a well-supported range for maximizing muscle mass and strength gains from resistance training.",
            "Total daily protein intake matters more than precise timing around workouts (the old 'anabolic window' is a minor effect at most).",
            "A caloric surplus supports muscle growth (bulking); a moderate deficit with high protein preserves muscle while losing fat (cutting).",
            "Protein needs scale up somewhat further for older adults or during aggressive fat-loss phases to protect lean mass.",
        ],
        citations=[
            PubMedCitation("28642676", "Jäger et al. (2017). International Society of Sports Nutrition Position Stand: protein and exercise."),
            PubMedCitation("28698222", "Morton et al. (2018). A systematic review, meta-analysis and meta-regression of the effect of protein supplementation on resistance training-induced gains in muscle mass and strength."),
            PubMedCitation("24299050", "Schoenfeld et al. (2013). The effect of protein timing on muscle strength and hypertrophy: a meta-analysis."),
            PubMedCitation("34673936", "Kirwan et al. (2022). Protein interventions augment the effect of resistance exercise on appendicular lean mass and handgrip strength in older adults."),
        ],
    ),
]
