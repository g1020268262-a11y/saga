----------------------------- MODULE SagaQuota -----------------------------
EXTENDS Integers, FiniteSets

(***************************************************************************
 Source-bound, single-token receiver-quota model of the unmodified code.
 Upstream: 7372111bea150e32cee390a616849316d2780bfc
 All source references below are to saga/agent.py unless stated otherwise.

 Scope: known token, fixed matching identity, stable expiry/policy, ordinary
 messages and responses, no token deletion/reissue, no network/LLM failures.
 B controls its own client; B's received_tokens balance is not an A-side guard.
 Each racing connection submits one request. PrefixUsed ordinary requests
 are executed explicitly on an earlier, sequential issuance connection.
 No Python refinement theorem or cryptographic proof is asserted.
***************************************************************************)

CONSTANTS InitialQuota, Connections, PrefixUsed, MetadataValid

ASSUME /\ InitialQuota \in Nat
       /\ IsFiniteSet(Connections)
       /\ Connections # {}
       /\ PrefixUsed \in 0..InitialQuota
       /\ PrefixUsed <= 100
       /\ MetadataValid \in BOOLEAN

VARIABLES remaining, accepted, backendCalls, pc, checkedRemaining,
          phase, prefixPC, prefixDone

vars == <<remaining, accepted, backendCalls, pc, checkedRemaining,
          phase, prefixPC, prefixDone>>

ConnectionStates == {"Entry", "Ready", "Checked", "Debited", "Done",
                     "Rejected", "EntryRejected"}
PrefixStates == {"Ready", "Checked", "Debited", "Done", "Rejected"}
FinalStates == {"Done", "Rejected", "EntryRejected"}

\* 321, 1102-1103: begin after a real token is issued and stored at A.
\* Unlike a compressed-prefix model, accepted ALWAYS starts at zero.
Init ==
    /\ remaining = InitialQuota
    /\ accepted = 0
    /\ backendCalls = 0
    /\ pc = [c \in Connections |-> "Entry"]
    /\ checkedRemaining = [c \in Connections |-> 0]
    /\ phase = "Prefix"
    /\ prefixPC = "Ready"
    /\ prefixDone = 0

\* 348-381: one successful check, with its lock released on return.
PrefixCheck ==
    /\ phase = "Prefix"
    /\ prefixPC = "Ready"
    /\ prefixDone < PrefixUsed
    /\ MetadataValid /\ remaining # 0
    /\ prefixPC' = "Checked"
    /\ UNCHANGED <<remaining, accepted, backendCalls, pc, checkedRemaining,
                    phase, prefixDone>>

PrefixReject ==
    /\ phase = "Prefix"
    /\ prefixPC = "Ready"
    /\ prefixDone < PrefixUsed
    /\ (~MetadataValid \/ remaining = 0)
    /\ prefixPC' = "Rejected"
    /\ phase' = "Aborted"
    /\ UNCHANGED <<remaining, accepted, backendCalls, pc, checkedRemaining,
                    prefixDone>>

\* 604-605: a DIFFERENT lock interval. There is no fresh quota check here.
\* The conditional is max(0, remaining - 1) over our nonnegative domain.
PrefixConsume ==
    /\ phase = "Prefix"
    /\ prefixPC = "Checked"
    /\ remaining' = IF remaining = 0 THEN 0 ELSE remaining - 1
    /\ accepted' = accepted + 1
    /\ prefixPC' = "Debited"
    /\ UNCHANGED <<backendCalls, pc, checkedRemaining, phase, prefixDone>>

\* 631, 634: project the ordinary successful prefix onto its backend-call
\* event and next iteration. PrefixUsed <= 100 keeps i > MAX_QUERIES false.
PrefixBackend ==
    /\ phase = "Prefix"
    /\ prefixPC = "Debited"
    /\ backendCalls' = backendCalls + 1
    /\ prefixDone' = prefixDone + 1
    /\ prefixPC' = "Ready"
    /\ UNCHANGED <<remaining, accepted, pc, checkedRemaining, phase>>

\* The prefix session can close without deleting the token (586-591).
\* Racing connections are subsequently allowed to perform the existing-
\* token entrance check at 1120. No existing quota is reset or invented.
BeginConnections ==
    /\ phase = "Prefix"
    /\ prefixPC = "Ready"
    /\ prefixDone = PrefixUsed
    /\ phase' = "Race"
    /\ prefixPC' = "Done"
    /\ UNCHANGED <<remaining, accepted, backendCalls, pc, checkedRemaining,
                    prefixDone>>

\* 1120-1128: existing-token entrance check, NOT a quota reservation.
Enter(c) ==
    /\ phase = "Race" /\ pc[c] = "Entry"
    /\ MetadataValid /\ remaining # 0
    /\ pc' = [pc EXCEPT ![c] = "Ready"]
    /\ UNCHANGED <<remaining, accepted, backendCalls, checkedRemaining,
                    phase, prefixPC, prefixDone>>

RejectEntry(c) ==
    /\ phase = "Race" /\ pc[c] = "Entry"
    /\ (~MetadataValid \/ remaining = 0)
    /\ pc' = [pc EXCEPT ![c] = "EntryRejected"]
    /\ UNCHANGED <<remaining, accepted, backendCalls, checkedRemaining,
                    phase, prefixPC, prefixDone>>

\* 595, 598, 348-381: every parsed message is checked again.
\* Non-quota checks are summarized by stable MetadataValid, never by
\* assuming token_is_valid itself is always true.
Check(c) ==
    /\ phase = "Race" /\ pc[c] = "Ready"
    /\ MetadataValid /\ remaining # 0
    /\ pc' = [pc EXCEPT ![c] = "Checked"]
    /\ checkedRemaining' = [checkedRemaining EXCEPT ![c] = remaining]
    /\ UNCHANGED <<remaining, accepted, backendCalls, phase, prefixPC,
                    prefixDone>>

Reject(c) ==
    /\ phase = "Race" /\ pc[c] = "Ready"
    /\ (~MetadataValid \/ remaining = 0)
    /\ pc' = [pc EXCEPT ![c] = "Rejected"]
    /\ UNCHANGED <<remaining, accepted, backendCalls, checkedRemaining,
                    phase, prefixPC, prefixDone>>

\* 604-605: guard only on the prior control location, not remaining > 0.
\* accepted is an observer of quota admission; it is NOT a native variable.
Consume(c) ==
    /\ phase = "Race" /\ pc[c] = "Checked"
    /\ remaining' = IF remaining = 0 THEN 0 ELSE remaining - 1
    /\ accepted' = accepted + 1
    /\ pc' = [pc EXCEPT ![c] = "Debited"]
    /\ UNCHANGED <<backendCalls, checkedRemaining, phase, prefixPC,
                    prefixDone>>

\* 609-634: ordinary message, first request on this connection (i = 0).
\* Record invocation separately from quota admission. Done means this
\* bounded observation is complete, not task completion or delivery.
InvokeBackend(c) ==
    /\ phase = "Race" /\ pc[c] = "Debited"
    /\ backendCalls' = backendCalls + 1
    /\ pc' = [pc EXCEPT ![c] = "Done"]
    /\ UNCHANGED <<remaining, accepted, checkedRemaining, phase, prefixPC,
                    prefixDone>>

Terminated ==
    \/ phase = "Aborted"
    \/ /\ phase = "Race"
       /\ \A c \in Connections : pc[c] \in FinalStates

\* Stutter ONLY at legitimate terminal states for TLC's Next exploration.
\* Deadlock checking remains enabled; unexpected nonterminal blocking is
\* not hidden by a global TRUE/UNCHANGED action or a -deadlock flag.
TerminalStutter == Terminated /\ UNCHANGED vars

Next ==
    \/ PrefixCheck
    \/ PrefixReject
    \/ PrefixConsume
    \/ PrefixBackend
    \/ BeginConnections
    \/ \E c \in Connections :
           Enter(c) \/ RejectEntry(c) \/ Check(c) \/ Reject(c)
           \/ Consume(c) \/ InvokeBackend(c)
    \/ TerminalStutter

Spec == Init /\ [][Next]_vars

TypeOK ==
    /\ remaining \in 0..InitialQuota
    /\ accepted \in 0..(PrefixUsed + Cardinality(Connections))
    /\ backendCalls \in 0..(PrefixUsed + Cardinality(Connections))
    /\ pc \in [Connections -> ConnectionStates]
    /\ checkedRemaining \in [Connections -> 0..InitialQuota]
    /\ phase \in {"Prefix", "Race", "Aborted"}
    /\ prefixPC \in PrefixStates
    /\ prefixDone \in 0..PrefixUsed

AdmittedConnections == {c \in Connections : pc[c] \in {"Debited", "Done"}}
BackendConnections == {c \in Connections : pc[c] = "Done"}
PendingPrefixAdmission == IF prefixPC = "Debited" THEN 1 ELSE 0

\* Structural sanity checks; these should hold EVEN when quota is exceeded.
SourceAccounting ==
    /\ accepted = prefixDone + PendingPrefixAdmission
                     + Cardinality(AdmittedConnections)
    /\ backendCalls = prefixDone + Cardinality(BackendConnections)
    /\ backendCalls <= accepted
    /\ remaining = IF accepted <= InitialQuota
                   THEN InitialQuota - accepted ELSE 0

QuotaSafety == accepted <= InitialQuota
BackendQuotaSafety == backendCalls <= InitialQuota

\* Witness queries, NOT desired safety requirements. A violation of one
\* below means its named event is reachable; configs label this explicitly.
NoAdmission == accepted = 0
NoMessageRejection == \A c \in Connections : pc[c] # "Rejected"

=============================================================================
