#====================================================================================================
# START - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================

# THIS SECTION CONTAINS CRITICAL TESTING INSTRUCTIONS FOR BOTH AGENTS
# BOTH MAIN_AGENT AND TESTING_AGENT MUST PRESERVE THIS ENTIRE BLOCK

# Communication Protocol:
# If the `testing_agent` is available, main agent should delegate all testing tasks to it.
#
# You have access to a file called `test_result.md`. This file contains the complete testing state
# and history, and is the primary means of communication between main and the testing agent.
#
# Main and testing agents must follow this exact format to maintain testing data. 
# The testing data must be entered in yaml format Below is the data structure:
# 
## user_problem_statement: {problem_statement}
## backend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.py"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## frontend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.js"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## metadata:
##   created_by: "main_agent"
##   version: "1.0"
##   test_sequence: 0
##   run_ui: false
##
## test_plan:
##   current_focus:
##     - "Task name 1"
##     - "Task name 2"
##   stuck_tasks:
##     - "Task name with persistent issues"
##   test_all: false
##   test_priority: "high_first"  # or "sequential" or "stuck_first"
##
## agent_communication:
##     -agent: "main"  # or "testing" or "user"
##     -message: "Communication message between agents"

# Protocol Guidelines for Main agent
#
# 1. Update Test Result File Before Testing:
#    - Main agent must always update the `test_result.md` file before calling the testing agent
#    - Add implementation details to the status_history
#    - Set `needs_retesting` to true for tasks that need testing
#    - Update the `test_plan` section to guide testing priorities
#    - Add a message to `agent_communication` explaining what you've done
#
# 2. Incorporate User Feedback:
#    - When a user provides feedback that something is or isn't working, add this information to the relevant task's status_history
#    - Update the working status based on user feedback
#    - If a user reports an issue with a task that was marked as working, increment the stuck_count
#    - Whenever user reports issue in the app, if we have testing agent and task_result.md file so find the appropriate task for that and append in status_history of that task to contain the user concern and problem as well 
#
# 3. Track Stuck Tasks:
#    - Monitor which tasks have high stuck_count values or where you are fixing same issue again and again, analyze that when you read task_result.md
#    - For persistent issues, use websearch tool to find solutions
#    - Pay special attention to tasks in the stuck_tasks list
#    - When you fix an issue with a stuck task, don't reset the stuck_count until the testing agent confirms it's working
#
# 4. Provide Context to Testing Agent:
#    - When calling the testing agent, provide clear instructions about:
#      - Which tasks need testing (reference the test_plan)
#      - Any authentication details or configuration needed
#      - Specific test scenarios to focus on
#      - Any known issues or edge cases to verify
#
# 5. Call the testing agent with specific instructions referring to test_result.md
#
# IMPORTANT: Main agent must ALWAYS update test_result.md BEFORE calling the testing agent, as it relies on this file to understand what to test next.

#====================================================================================================
# END - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================



#====================================================================================================
# Testing Data - Main Agent and testing sub agent both should log testing data below this section
#====================================================================================================
user_problem_statement: "PAUSE — Home restyle (carousel categorie, bottom bar glass a tema, sfondo atmosferico, bordi luminosi) + nuova schermata Premium (prezzi €3,99 / €29,99 con claim €2,49/mese / €49,99, confronto Gratis vs Premium con sole funzioni reali) + onboarding snello (genere/età dietro link facoltativo)."

current_request: "Generare Mi piace/Salva/Condividi con lo stesso AI delle altre icone 3D; correggere realmente transizione Home↔Reader (titolo sparisce e card scatta)."
latest_request: "Condividi = freccia fuori riquadro 3D; bottom bar tutta 3D riusando nuovo bookmark; Esplora Home interamente dentro contenitore."
navigation_icon_verification:
  implemented: true
  working: true
  needs_retesting: false
  priority: "high"
  result: "iteration_8 + follow-up PASS. Explicit aria-selected fixed and verified for all four tabs. Native share sheet remains device-only validation."
  files: "glass-tab-bar.tsx, tab-icon-3d.tsx, icon-3d-assets.ts, action-icon-3d.tsx, home-controls.tsx"
  test_plan:
    - "All four tabs navigate, labels/testIDs unchanged, animated base/active icon states, ≥44pt tap targets."
    - "Saved bottom bar and Save ending use EXACT same bookmark asset pair."
    - "Home Explore art wholly contained with margins, no text overlap or horizontal overflow at 320/390/430."
    - "Ending Share displays new standard arrow out of square, handler unchanged. Native sheet requires physical device."
    - "No asset white/black rectangular backgrounds; no bundling/runtime errors. Home↔Reader regression."
current_verification:
  - task: "3D action icons and persistent like/bookmark/share"
    implemented: true
    working: true
    needs_retesting: false
    priority: "high"
    status_history:
      - agent: "main"
        comment: "Existing Gemini model verified. 5 bundled RGBA assets archived to managed storage and download hashes checked. Neutral states derived from active silhouettes to eliminate damaged edges/shape jump. ActionIcon3D has complementary fade, bounce, 44pt targets, state testIDs."
  - task: "Home↔Reader continuous title/cover"
    implemented: true
    working: true
    needs_retesting: false
    priority: "high"
    stuck_count: 2
    status_history:
      - agent: "user"
        comment: "Titolo scompare/ricompare, card scatta; animazione deve funzionare bene."
      - agent: "main"
        comment: "Matched Home font; title/grid copies now share one geometric track and complementary opacities; text above cover; Premium CTA included in measured intro. Close uses reader's measured cover and fresh Home rect; no premature fade. Removed stale reader dismiss timer. Morph open skips progress auto-resume. Back from chapters/end stays simple. Need frame sampling + screenshots and persistent action tests."
      - agent: "main"
        working: true
        comment: "Final mobile-web follow-up PASS. Fixed initial React/UI-style paint race. 4 open-close cycles across 390x844/375x667: 380 visible frames, zero missing titles, trajectories coincide, zero overlays left. Chapter/end simple back PASS; actions/persistence PASS; backend 5/5. See iteration_7_followup.json; native gesture/share/fluidity still require physical device acceptance."

frontend:
  - task: "Home: carousel orizzontale categorie + indicatore, rimozione Vedi tutte"
    implemented: true
    working: "NA"
    file: "frontend/app/(tabs)/discover.tsx, frontend/src/components/home-category-carousel.tsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Griglia 2x4 sostituita da Animated.ScrollView orizzontale (testID home-category-list, home-category-carousel, home-category-indicator). Tap tessera = toggle come prima (toast 'almeno una' come overlay)."
  - task: "Bottom bar glass custom (GlassTabBar) con colore del tema"
    implemented: true
    working: "NA"
    file: "frontend/src/components/glass-tab-bar.tsx, frontend/app/(tabs)/_layout.tsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: "tabBar custom; testID tab-home/tab-explore/tab-saved/tab-profile preservati. Icona Argomenti = albums."
  - task: "Sfondo atmosferico Home (HomeBackdrop) + bordi luminosi card"
    implemented: true
    working: "NA"
    file: "frontend/src/components/home-backdrop.tsx, home-story-card.tsx, home-controls.tsx, resume-card.tsx, story-morph.tsx"
    stuck_count: 0
    priority: "medium"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Backdrop generativo con colors.atmos*; bordi con colors.brand."
  - task: "Schermata Premium v3 (prezzi nuovi, claim €2,49/mese, tabella confronto)"
    implemented: true
    working: "NA"
    file: "frontend/app/premium.tsx, frontend/src/premium.ts, frontend/src/i18n.tsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: "testID: paywall-hero, paywall-claim, plan-monthly/yearly/lifetime, plan-hint, paywall-compare, premium-activate, premium-cancel, premium-close."
  - task: "Onboarding profilo snello (genere/età dietro 'Aggiungi dettagli')"
    implemented: true
    working: "NA"
    file: "frontend/src/components/onboarding-profile.tsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: "testID onboarding-profile-more toggla le card genere/età."

metadata:
  created_by: "main_agent"
  version: "1.0"
  test_sequence: 1

test_plan:
  current_focus:
    - "Home carousel + tab bar + premium + onboarding"
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

agent_communication:
  - agent: "main"
    message: "Solo frontend da testare (backend non toccato). Onboarding: Continua come ospite -> scegli argomenti -> Continua -> Home."

  - task: "Home deck: card a tutta altezza + dati (StoryInfoGrid) sotto la card con dissolvenza + indicatore asimmetrico DeckProgress"
    implemented: true
    working: "NA"
    file: "frontend/src/components/home-story-deck.tsx, deck-badges.tsx, deck-progress.tsx, story-morph.tsx, home-story-card.tsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: "testID deck-badges, home-story-meta, discover-deck-dots, discover-deck-dot-active, discover-deck-dot-N (passate), discover-deck-continue. Morph verso lettore aggiornato (dati partono da sotto la card)."
