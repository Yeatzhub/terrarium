# Hub Navigation Audit Report

## Summary
Analyzed compiled Next.js build output. Found **16 navigation issues** across 3 priority levels.

---

## Critical Issues (HIGH)

### 1. Mobile "More" Button Non-Functional
- **Location:** All pages - Mobile bottom navigation
- **Issue:** `<button>` with no `onClick` handler
- **Impact:** Mobile users can't access: Action Items, Hardware, LLM, Notes, Tasks, Chat
- **Fix:** Add drawer/sheet for additional navigation

### 2. Mobile Menu Toggle Non-Functional
- **Location:** Sidebar header
- **Issue:** Hamburger button shows but sidebar won't open on mobile
- **Fix:** Add state to toggle sidebar visibility

### 3. Dead Links in Trading Page
- **Location:** `/trading` - Quick Actions section
- **Dead Routes:** `/trading/history`, `/trading/settings`, `/trading/api-keys`
- **Fix:** Create pages or remove links

---

## Medium Issues

| Issue | Location | Fix |
|-------|----------|-----|
| Missing sidebar items | Routes exist but not in sidebar | Add `/action-items`, `/chat`, `/tasks`, `/trading/test` |
| LLM submenu missing | Chevron exists but no items | Add dropdown with links |
| Sidebar collapse broken | Collapse button | Add toggle handler |
| Inconsistent back buttons | Some have, some don't | Standardize |
| LLM route inconsistency | Sidebar → `/llm/status` but `/llm` exists | Choose one |

---

## Dead Routes

| Route | Source | Action |
|-------|--------|--------|
| `/trading/history` | Quick Actions | Create or remove |
| `/trading/settings` | Quick Actions | Create or remove |
| `/trading/api-keys` | Quick Actions | Create or remove |

---

## Verified Working Pages

| Route | In Sidebar | Has Back Button |
|-------|------------|-----------------|
| `/` | ✅ | N/A |
| `/agents` | ✅ | ⚠️ CSR issue |
| `/hardware` | ✅ | ⚠️ CSR issue |
| `/llm/status` | ✅ | ✅ |
| `/notes` | ✅ | ✅ |
| `/trading` | ✅ | ✅ |
| `/trading/bot/pionex-xrp` | ✅ submenu | ⚠️ CSR issue |
| `/action-items` | ❌ Missing | ✅ |
| `/chat` | ❌ Missing | ✅ |
| `/tasks` | ❌ Missing | ✅ |

---

## Recommendations

1. **Immediate (High Priority):**
   - Fix mobile navigation (biggest UX impact)
   - Remove dead trading links

2. **Short-term (Medium Priority):**
   - Add LLM submenu
   - Add missing sidebar items
   - Implement sidebar collapse

3. **Long-term (Low Priority):**
   - Standardize back buttons
   - Improve mobile UX overall