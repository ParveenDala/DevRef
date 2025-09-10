import itertools
import re
from typing import Dict, List


def normalize(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.strip().lower())


def extract_topics(comment: str) -> Dict[str, List[str]]:
    text = normalize(comment)
    topics = []
    keywords = []
    intents = []

    for key, syns in SYNONYMS.items():
        if key in text or any(s in text for s in syns):
            topics.append(key)

    for hint in STACK_HINTS:
        if hint in text:
            keywords.append(hint)

    if any(w in text for w in ["prefer", "instead", "should use"]):
        intents.append("replace-tech")
    if any(w in text for w in ["avoid", "anti-pattern", "don't", "do not"]):
        intents.append("avoid-pattern")
    if any(w in text for w in ["inject", "di", "dependency injection"]):
        intents.append("apply-di")

    if not topics and "repository" in text:
        topics.append("repository pattern")

    return {"topics": sorted(set(topics)), "keywords": sorted(set(keywords)), "intents": sorted(set(intents))}


def build_queries(extraction: Dict[str, List[str]]) -> List[str]:
    raw_topics = extraction.get("topics") or []
    intents = [i.lower() for i in (extraction.get("intents") or [])]

    # Normalize and keep order — lowercase, strip, unique
    seen = set()
    topics = []
    for t in raw_topics:
        if not t:
            continue
        tt = t.strip()
        if not tt:
            continue
        tl = tt if isinstance(tt, str) else str(tt)
        tl = tl.strip()
        key = tl.lower()
        if key not in seen:
            seen.add(key)
            topics.append(tl)

    if not topics:
        return []

    queries = []

    # helpers
    def add(q):
        q = q.strip()
        if q and q.lower() not in (x.lower() for x in queries):
            queries.append(q)

    def combos_of_two(items):
        return list(itertools.combinations(items, 2))

    # Make a compact joined stack string like "Compose Android Kotlin"
    stack_join = " ".join(
        [t for t in topics if t.lower() not in ("android",)]).strip()  # keep Android out of stack_join if present
    full_context = " ".join(topics).strip()  # everything

    # Intent-aware templates
    if "replace-tech" in intents or "migrate" in intents or "migration" in intents:
        # If we have at least two topics, produce migrate/replace queries for pairwise combinations
        pairs = combos_of_two(topics)
        for a, b in pairs:
            add(f"migrate from {a} to {b} Android Kotlin")
            add(f"migrate {a} to {b} tutorial")
            add(f"replace {a} with {b} Android")
            add(f"{b} migration guide (from {a})")
            add(f"{a} vs {b} (pros and cons)")
            # YouTube-friendly
            add(f"{a} to {b} migration tutorial youtube")
            add(f"{b} vs {a} comparison youtube")
        # also general migration queries
        add(f"{full_context} migration guide")
        add(f"{full_context} replace tutorial")
    # Comparison / evaluation intent
    if "compare" in intents or "evaluation" in intents or "vs" in intents:
        pairs = combos_of_two(topics)
        for a, b in pairs:
            add(f"{a} vs {b} Android Kotlin")
            add(f"{a} vs {b} performance comparison")
            add(f"{a} vs {b} tutorial")
            add(f"{a} vs {b} youtube")
    # Learning / tutorials intent
    if "learn" in intents or "howto" in intents or "tutorial" in intents or not intents:
        # default: for each topic, generate common helpful queries
        for t in topics:
            add(f"{t} tutorial")
            add(f"{t} guide")
            add(f"{t} best practices")
            add(f"{t} implementation example")
            add(f"{t} android kotlin tutorial")
            add(f"{t} youtube tutorial")
            add(f"{t} github examples")
            add(f"{t} official docs")
            add(f"{t} site:developer.android.com")
            add(f"{t} site:github.com")
    # Best-practices / architecture / production intent
    if "best-practices" in intents or "architecture" in intents or "production" in intents:
        for t in topics:
            add(f"{t} best practices")
            add(f"{t} architecture patterns")
            add(f"{t} production ready")
            add(f"{t} performance optimization")
    # Examples / snippets / github
    if "example" in intents or "examples" in intents or "code" in intents:
        for t in topics:
            add(f"{t} code example")
            add(f"{t} sample project github")
            add(f"{t} example implementation")
    # Official docs / authoritative sources
    add(f"{full_context} official docs")
    add(f"{stack_join} official docs" if stack_join else None)
    add(f"{full_context} developer.android.com")
    add(f"{full_context} github examples")

    # Add a couple of high-value cross queries combining main topics and typical helpful terms
    add(f"{full_context} best practices guide")
    add(f"{full_context} tutorial android kotlin")
    add(f"{full_context} migration guide")
    add(f"{full_context} comparison")
    add(f"{full_context} youtube tutorial")

    # Final cleanup & dedupe while preserving order and removing Nones
    cleaned = []
    seen_lower = set()
    for q in queries:
        if not q:
            continue
        q_s = " ".join(q.split())  # collapse whitespace
        kl = q_s.lower()
        if kl not in seen_lower:
            seen_lower.add(kl)
            cleaned.append(q_s)
    return cleaned


SYNONYMS = {
    # Languages
    "kotlin": ["kt", "kotlin lang", "kotlin language"],
    "java": ["java lang", "jdk", "jvm language"],

    # Core / Android
    "android": ["android sdk", "android os", "android platform"],
    "jetpack": ["androidx", "jetpack libraries"],
    "appcompat": ["androidx appcompat"],
    "lifecycle": ["androidx lifecycle", "livedata"],
    "viewmodel": ["androidx viewmodel", "vm"],
    "navigation": ["jetpack navigation", "nav component", "navigation component"],
    "workmanager": ["jetpack workmanager", "background work", "android work"],
    "room": ["jetpack room", "sqlite orm", "room db", "room database"],
    "datastore": ["jetpack datastore", "preferences datastore", "proto datastore"],
    "paging": ["paging3", "paging library", "jetpack paging"],

    # UI
    "compose": ["jetpack compose", "android compose", "compose ui", "compose toolkit"],
    "xml": ["android xml", "xml layout", "layout xml"],
    "constraintlayout": ["constraint layout"],
    "motionlayout": ["motion layout"],
    "material3": ["m3", "material you", "material design 3"],
    "glance": ["jetpack glance", "app widgets"],
    "wearOS": ["wear os", "android wear", "wearable"],
    "tvOS": ["android tv", "tv app"],

    # Dependency Injection
    "hilt": ["dagger hilt", "android hilt"],
    "dagger": ["dagger2", "dagger 2", "dagger framework"],
    "koin": ["koin di", "koin framework"],
    "dependency injection": ["di", "injection"],

    # Async / Concurrency
    "coroutines": ["coroutine", "kotlin coroutines", "kotlin coroutine"],
    "flow": ["kotlin flow", "stateflow", "sharedflow"],
    "rxjava": ["rx", "reactive java"],
    "rxkotlin": ["rx kotlin"],

    # Networking
    "retrofit": ["retrofit2", "retrofit 2"],
    "okhttp": ["okhttp3", "ok http", "okhttp 3"],
    "ktor": ["ktor client", "ktor server"],
    "volley": ["android volley"],
    "graphql": ["graph ql"],
    "apollo": ["apollo graphql"],

    # Serialization
    "moshi": ["moshi json", "square moshi"],
    "gson": ["google gson", "gson json"],
    "kotlinx-serialization": ["kotlin serialization", "kotlinx serialization"],

    # Architecture Patterns
    "mvvm": ["model view viewmodel"],
    "mvi": ["model view intent"],
    "mvc": ["model view controller"],
    "clean-architecture": ["clean architecture"],
    "modularization": ["modular app", "multi module"],

    # Testing
    "junit": ["junit4", "junit5", "junit 4", "junit 5"],
    "espresso": ["android espresso", "ui espresso"],
    "robolectric": ["android robolectric"],
    "mockk": ["mock k", "mock kotlin"],
    "truth": ["google truth"],
    "turbine": ["flow testing", "turbine test"],
    "ui-automator": ["uiautomator", "ui automator"],
    "kaspresso": ["kaspresso ui test"],
    "kotest": ["kotlin test", "kotlin testing"],

    # Build Tools
    "gradle": ["gradle build", "gradle android"],
    "ksp": ["kotlin symbol processing"],
    "kapt": ["kotlin annotation processing"],
    "bazel": ["bazel build"],

    # Analytics & Monitoring
    "firebase-analytics": ["firebase analytics"],
    "crashlytics": ["firebase crashlytics"],
    "datadog": ["datadog monitoring"],
    "newrelic": ["new relic"],
    "sentry": ["sentry logging"],
    "appcenter": ["microsoft appcenter"],

    # Ads & Monetization
    "admob": ["google admob"],
    "facebook-ads": ["meta ads", "fb ads"],
    "applovin": ["app lovin"],
    "ironSource": ["iron source"],

    # Push & Messaging
    "firebase-messaging": ["fcm", "firebase cloud messaging"],
    "onesignal": ["one signal"],
    "pubnub": ["pub nub"],
    "pusher": ["pusher channels"],

    # Storage & Database
    "sqlite": ["sql lite"],
    "realm": ["realm db", "realm database"],
    "objectbox": ["object box"],

    # Multimedia
    "exoplayer": ["exo player"],
    "media3": ["androidx media3"],
    "ffmpeg": ["ffmpeg library"],
    "opengl": ["open gl", "open graphics library"],
    "sceneform": ["scene form"],
    "arcore": ["ar core"],

    # Security
    "keystore": ["android keystore", "keystore system"],
    "safetynet": ["safety net"],
    "playintegrity": ["play integrity api"],
    "proguard": ["pro guard"],
    "r8": ["android r8"],

    # Cloud / Backend
    "firebase": ["firebase sdk", "firebase services"],
    "supabase": ["supabase backend"],
    "amplify": ["aws amplify"],
    "socketio": ["socket io"],

    # DevOps / CI/CD
    "fastlane": ["fast lane"],
    "bitrise": ["bitrise ci"],
    "circleci": ["circle ci"],
    "github-actions": ["github actions"],

    # Popular Libraries
    "glide": ["glide image loader"],
    "coil": ["coil image loader", "coil kt"],
    "picasso": ["picasso image loader"],
    "lottie": ["lottie animations", "airbnb lottie"],
    "timber": ["timber logging"],
    "shimmer": ["facebook shimmer"],
    "stetho": ["facebook stetho"],
    "leakcanary": ["leak canary", "square leakcanary"]
}

STACK_HINTS = [
    # Core Languages
    "kotlin", "java",

    # Android Core & Jetpack
    "android", "jetpack", "appcompat", "androidx", "lifecycle",
    "viewmodel", "navigation", "workmanager", "room", "datastore",
    "paging", "cameraX", "mlkit", "biometric", "slices",

    # UI
    "compose", "xml", "constraintlayout", "motionlayout",
    "material3", "glance", "wearOS", "tvOS",

    # Dependency Injection
    "hilt", "dagger", "koin",

    # Async / Concurrency
    "coroutines", "flow", "rxjava", "rxkotlin",

    # Networking
    "retrofit", "okhttp", "ktor", "volley", "graphql", "apollo",

    # Serialization
    "moshi", "gson", "kotlinx-serialization",

    # Architecture Patterns
    "mvvm", "mvi", "mvc", "clean-architecture", "modularization",

    # Testing
    "junit", "espresso", "robolectric", "mockk", "truth", "turbine",
    "ui-automator", "kaspresso", "kotest",

    # Build Tools
    "gradle", "ksp", "kapt", "bazel",

    # Analytics & Monitoring
    "firebase-analytics", "crashlytics", "datadog", "newrelic",
    "sentry", "appcenter",

    # Ads & Monetization
    "admob", "facebook-ads", "applovin", "ironSource",

    # Push Notifications & Messaging
    "firebase-messaging", "onesignal", "pubnub", "pusher",

    # Storage & Database
    "sqlite", "realm", "objectbox",

    # Multimedia
    "exoplayer", "media3", "ffmpeg", "opengl", "sceneform", "arcore",

    # Security
    "keystore", "safetynet", "playintegrity", "proguard", "r8",

    # Cloud / Backend Integration
    "firebase", "supabase", "amplify", "graphql", "socketio",

    # DevOps & CI/CD
    "fastlane", "bitrise", "circleci", "github-actions",

    # Other Popular Libraries
    "glide", "coil", "picasso", "lottie", "timber", "dagger2",
    "shimmer", "stetho", "leakcanary"
]
