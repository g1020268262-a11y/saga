------------------------- MODULE SagaQuotaDelivery -------------------------
EXTENDS Integers, FiniteSets

(***************************************************************************
 Original-code extension: BOTH endpoint ledgers, repeated ordinary requests,
 request/response delivery and bounded connection failures. No PrefixUsed.
 Upstream: 7372111bea150e32cee390a616849316d2780bfc (saga/agent.py).

 Known, stable token and identity; no expiry/deletion/reissue. Existing-token
 entry check is explicit. At most one outstanding request per connection;
 different connections interleave and share the two endpoint ledgers.
 Network abort is an explicit ENVIRONMENT assumption, not silent packet loss
 on an otherwise healthy TCP connection. No ACK/refund/retry is invented.
 QuiescentAgreement/NoUnadmittedConsumption are CANDIDATE accounting goals,
 not properties already promised or proved by the original SAGA paper.
***************************************************************************)

CONSTANTS InitialQuota, Connections, MaxRequests, MetadataValid,
          FaultModes, MaxFaults

FaultKinds == {"RequestAbort", "ResponseAbort", "SendError"}

ASSUME /\ InitialQuota \in Nat
       /\ IsFiniteSet(Connections) /\ Connections # {}
       /\ MaxRequests \in 1..100
       /\ MetadataValid \in BOOLEAN
       /\ FaultModes \subseteq FaultKinds
       /\ MaxFaults \in 0..Cardinality(Connections)

VARIABLES senderRemaining, receiverRemaining, bpc, apc, link, counts,
          faultCount

vars == <<senderRemaining, receiverRemaining, bpc, apc, link, counts,
          faultCount>>

BStates == {"Entry", "Ready", "Checked", "Debit", "Waiting", "Done",
            "Failed", "QuotaStopped", "EntryRejected"}
AStates == {"Entry", "Read", "Parsed", "Checked", "Debited", "Reply",
            "Stopped", "Rejected", "EntryRejected"}
BFinal == {"Done", "Failed", "QuotaStopped", "EntryRejected"}
AFinal == {"Stopped", "Rejected", "EntryRejected"}

RECURSIVE SumOn(_, _)
SumOn(f, domain) ==
    IF domain = {} THEN 0
    ELSE LET c == CHOOSE item \in domain : TRUE
         IN f[c] + SumOn(f, domain \ {c})

Writes == SumOn([c \in Connections |-> counts[c].writes], Connections)
SenderDebits == SumOn([c \in Connections |-> counts[c].senderDebits], Connections)
Accepted == SumOn([c \in Connections |-> counts[c].admits], Connections)
BackendCalls == SumOn([c \in Connections |-> counts[c].calls], Connections)
Replies == SumOn([c \in Connections |-> counts[c].replies], Connections)
Clamp(n) == IF n < 0 THEN 0 ELSE n

\* Init: both token dictionaries already store the SAME initial quota.
\* A: 1102-1103; B: 871-874 and 424-425. No prior consumption assumed.
Init ==
    /\ senderRemaining = InitialQuota
    /\ receiverRemaining = InitialQuota
    /\ bpc = [c \in Connections |-> "Entry"]
    /\ apc = [c \in Connections |-> "Entry"]
    /\ link = [c \in Connections |->
          [open |-> TRUE, request |-> FALSE, response |-> FALSE, fault |-> "None"]]
    /\ counts = [c \in Connections |->
          [writes |-> 0, senderDebits |-> 0, admits |-> 0,
           calls |-> 0, replies |-> 0]]
    /\ faultCount = 0
\* 两份余额都从初始额度开始。link 是有序、每方向最多一个待处理应用帧的抽象。
\* counts 是观察记录，不向原生消息添加请求编号、ACK 或退款协议。

\* 1120-1128: existing-token entrance; non-quota credential checks fixed.
AEnter(c) ==
    /\ apc[c] = "Entry" /\ bpc[c] = "Entry" /\ link[c].open
    /\ MetadataValid /\ receiverRemaining # 0
    /\ apc' = [apc EXCEPT ![c] = "Read"]
    /\ bpc' = [bpc EXCEPT ![c] = "Ready"]
    /\ UNCHANGED <<senderRemaining, receiverRemaining, link, counts, faultCount>>

ARejectEntry(c) ==
    /\ apc[c] = "Entry" /\ bpc[c] = "Entry" /\ link[c].open
    /\ (~MetadataValid \/ receiverRemaining = 0)
    /\ apc' = [apc EXCEPT ![c] = "EntryRejected"]
    /\ bpc' = [bpc EXCEPT ![c] = "EntryRejected"]
    /\ link' = [link EXCEPT ![c].open = FALSE]
    /\ UNCHANGED <<senderRemaining, receiverRemaining, counts, faultCount>>
\* 这里保留 A 的入口检查；进入会话不预留、不扣减额度。

\* 505-509, 392-413: B checks its own local token metadata and balance.
BCheck(c) ==
    /\ bpc[c] = "Ready" /\ counts[c].writes < MaxRequests
    /\ MetadataValid /\ senderRemaining # 0
    /\ bpc' = [bpc EXCEPT ![c] = "Checked"]
    /\ UNCHANGED <<senderRemaining, receiverRemaining, apc, link, counts, faultCount>>

BStopQuota(c) ==
    /\ bpc[c] = "Ready" /\ counts[c].writes < MaxRequests
    /\ (~MetadataValid \/ senderRemaining = 0)
    /\ bpc' = [bpc EXCEPT ![c] = "QuotaStopped"]
    /\ link' = [link EXCEPT ![c].open = FALSE]
    /\ UNCHANGED <<senderRemaining, receiverRemaining, apc, counts, faultCount>>

\* 513, 447-456: the complete local send call RETURNS NORMALLY.
\* This is not an application-level receipt by A. A can parse the queued
\* frame before B's separate local debit, but not before this abstraction point.
BSendReturn(c) ==
    /\ bpc[c] = "Checked" /\ link[c].open
    /\ ~link[c].request /\ ~link[c].response
    /\ bpc' = [bpc EXCEPT ![c] = "Debit"]
    /\ link' = [link EXCEPT ![c].request = TRUE]
    /\ counts' = [counts EXCEPT ![c].writes = @ + 1]
    /\ UNCHANGED <<senderRemaining, receiverRemaining, apc, faultCount>>

\* 518-519: local debit AFTER a successful send return, even if a reset
\* has meanwhile happened. No connection-open or receiver-ACK guard exists.
BDebit(c) ==
    /\ bpc[c] = "Debit"
    /\ senderRemaining' = Clamp(senderRemaining - 1)
    /\ counts' = [counts EXCEPT ![c].senderDebits = @ + 1]
    /\ bpc' = [bpc EXCEPT ![c] = "Waiting"]
    /\ UNCHANGED <<receiverRemaining, apc, link, faultCount>>
\* 发送返回与 B 扣减也分成两步；A 可以在两步之间执行。不会要求两端实时相等。

\* 586, 470-478, 595: A receives and parses a whole ordinary request.
AReceive(c) ==
    /\ apc[c] = "Read" /\ link[c].open /\ link[c].request
    /\ link' = [link EXCEPT ![c].request = FALSE]
    /\ apc' = [apc EXCEPT ![c] = "Parsed"]
    /\ UNCHANGED <<senderRemaining, receiverRemaining, bpc, counts, faultCount>>

\* 598, 348-381: message check; lock is RELEASED on successful return.
ACheck(c) ==
    /\ apc[c] = "Parsed"
    /\ MetadataValid /\ receiverRemaining # 0
    /\ apc' = [apc EXCEPT ![c] = "Checked"]
    /\ UNCHANGED <<senderRemaining, receiverRemaining, bpc, link, counts, faultCount>>

\* 598-601, 1141-1145: reject this message and close its connection.
AReject(c) ==
    /\ apc[c] = "Parsed"
    /\ (~MetadataValid \/ receiverRemaining = 0)
    /\ apc' = [apc EXCEPT ![c] = "Rejected"]
    /\ link' = [link EXCEPT ![c].open = FALSE,
                          ![c].request = FALSE, ![c].response = FALSE]
    /\ UNCHANGED <<senderRemaining, receiverRemaining, bpc, counts, faultCount>>

\* 604-605: separate receiver debit. Preserve the original missing recheck.
ADebit(c) ==
    /\ apc[c] = "Checked"
    /\ receiverRemaining' = Clamp(receiverRemaining - 1)
    /\ counts' = [counts EXCEPT ![c].admits = @ + 1]
    /\ apc' = [apc EXCEPT ![c] = "Debited"]
    /\ UNCHANGED <<senderRemaining, bpc, link, faultCount>>

\* 631-634: ordinary backend path, without a connection-open check.
ABackend(c) ==
    /\ apc[c] = "Debited"
    /\ counts' = [counts EXCEPT ![c].calls = @ + 1]
    /\ apc' = [apc EXCEPT ![c] = "Reply"]
    /\ UNCHANGED <<senderRemaining, receiverRemaining, bpc, link, faultCount>>
\* A 已经解析并准入的请求，即使连接随后中断，仍可继续走后端路径。

\* 643: response send returns normally; it does not debit either ledger.
AReplyReturn(c) ==
    /\ apc[c] = "Reply" /\ link[c].open
    /\ link' = [link EXCEPT ![c].response = TRUE]
    /\ apc' = [apc EXCEPT ![c] = "Read"]
    /\ UNCHANGED <<senderRemaining, receiverRemaining, bpc, counts, faultCount>>

\* 643 -> exception/handler exit: receiver had admitted the request already.
AReplyError(c) ==
    /\ apc[c] = "Reply" /\ ~link[c].open
    /\ apc' = [apc EXCEPT ![c] = "Stopped"]
    /\ UNCHANGED <<senderRemaining, receiverRemaining, bpc, link, counts, faultCount>>

\* 586-591: read failure before a complete parsed request => no A debit.
AReadError(c) ==
    /\ apc[c] = "Read" /\ ~link[c].open
    /\ apc' = [apc EXCEPT ![c] = "Stopped"]
    /\ UNCHANGED <<senderRemaining, receiverRemaining, bpc, link, counts, faultCount>>

\* 535, 542-543, 564-567: ordinary response, then another bounded request.
BReceiveResponse(c) ==
    /\ bpc[c] = "Waiting" /\ link[c].response
    /\ link' = [link EXCEPT ![c].response = FALSE]
    /\ counts' = [counts EXCEPT ![c].replies = @ + 1]
    /\ bpc' = [bpc EXCEPT ![c] = "Ready"]
    /\ UNCHANGED <<senderRemaining, receiverRemaining, apc, faultCount>>

\* 535-540: no response; return False WITHOUT restoring B's local quota.
BReceiveError(c) ==
    /\ bpc[c] = "Waiting" /\ ~link[c].open /\ ~link[c].response
    /\ bpc' = [bpc EXCEPT ![c] = "Failed"]
    /\ UNCHANGED <<senderRemaining, receiverRemaining, apc, link, counts, faultCount>>
\* 此处保留源码的“不退款”路径；并未把退款作为模型的预设修复。

BSendInterrupted(c) ==
    /\ bpc[c] = "Checked" /\ ~link[c].open
    /\ bpc' = [bpc EXCEPT ![c] = "Failed"]
    /\ UNCHANGED <<senderRemaining, receiverRemaining, apc, link, counts, faultCount>>

\* Bounded-input ENVIRONMENT: after MaxRequests ordinary responses, close
\* the connection instead of inventing an unbounded next input/task-finished token.
StopAtBound(c) ==
    /\ bpc[c] = "Ready" /\ counts[c].writes = MaxRequests
    /\ bpc' = [bpc EXCEPT ![c] = "Done"]
    /\ link' = [link EXCEPT ![c].open = FALSE]
    /\ UNCHANGED <<senderRemaining, receiverRemaining, apc, counts, faultCount>>

\* ENVIRONMENT: after normal local send return, the connection aborts before
\* A can parse this request. This is a lost application frame on reset,
\* not a recoverable individual TCP packet drop. BDebit remains enabled.
AbortRequest(c) ==
    /\ "RequestAbort" \in FaultModes /\ faultCount < MaxFaults
    /\ link[c].open /\ link[c].request /\ apc[c] = "Read"
    /\ link' = [link EXCEPT ![c].open = FALSE, ![c].request = FALSE,
                          ![c].response = FALSE, ![c].fault = "RequestAbort"]
    /\ faultCount' = faultCount + 1
    /\ UNCHANGED <<senderRemaining, receiverRemaining, bpc, apc, counts>>

\* ENVIRONMENT: A has admitted the current request, but B has not received
\* its response. Failure may precede the backend call, response send, or read.
AbortResponse(c) ==
    /\ "ResponseAbort" \in FaultModes /\ faultCount < MaxFaults
    /\ link[c].open
    /\ (apc[c] \in {"Debited", "Reply"} \/ link[c].response)
    /\ link' = [link EXCEPT ![c].open = FALSE, ![c].request = FALSE,
                          ![c].response = FALSE, ![c].fault = "ResponseAbort"]
    /\ faultCount' = faultCount + 1
    /\ UNCHANGED <<senderRemaining, receiverRemaining, bpc, apc, counts>>

\* ENVIRONMENT/control: sendall raises BEFORE any complete request frame
\* becomes available. This is ONE send-error case, not all possible send errors.
\* 513 raises before 518-519, so B does not execute its local debit.
SendErrorBeforeFrame(c) ==
    /\ "SendError" \in FaultModes /\ faultCount < MaxFaults
    /\ bpc[c] = "Checked" /\ link[c].open
    /\ link' = [link EXCEPT ![c].open = FALSE, ![c].request = FALSE,
                          ![c].response = FALSE, ![c].fault = "SendError"]
    /\ bpc' = [bpc EXCEPT ![c] = "Failed"]
    /\ faultCount' = faultCount + 1
    /\ UNCHANGED <<senderRemaining, receiverRemaining, apc, counts>>

Terminated ==
    \A c \in Connections :
        /\ bpc[c] \in BFinal /\ apc[c] \in AFinal
        /\ ~link[c].open /\ ~link[c].request /\ ~link[c].response

TerminalStutter == Terminated /\ UNCHANGED vars

Next ==
    \/ \E c \in Connections :
           AEnter(c) \/ ARejectEntry(c) \/ BCheck(c) \/ BStopQuota(c)
           \/ BSendReturn(c) \/ BDebit(c) \/ AReceive(c) \/ ACheck(c)
           \/ AReject(c) \/ ADebit(c) \/ ABackend(c) \/ AReplyReturn(c)
           \/ AReplyError(c) \/ AReadError(c) \/ BReceiveResponse(c)
           \/ BReceiveError(c) \/ BSendInterrupted(c) \/ StopAtBound(c)
           \/ AbortRequest(c) \/ AbortResponse(c) \/ SendErrorBeforeFrame(c)
    \/ TerminalStutter

Spec == Init /\ [][Next]_vars

TypeOK ==
    /\ senderRemaining \in 0..InitialQuota /\ receiverRemaining \in 0..InitialQuota
    /\ bpc \in [Connections -> BStates] /\ apc \in [Connections -> AStates]
    /\ link \in [Connections ->
          [open : BOOLEAN, request : BOOLEAN, response : BOOLEAN,
           fault : (FaultKinds \cup {"None"})]]
    /\ counts \in [Connections ->
          [writes : 0..MaxRequests, senderDebits : 0..MaxRequests,
           admits : 0..MaxRequests, calls : 0..MaxRequests, replies : 0..MaxRequests]]
    /\ faultCount \in 0..MaxFaults

SourceAccounting ==
    /\ senderRemaining = Clamp(InitialQuota - SenderDebits)
    /\ receiverRemaining = Clamp(InitialQuota - Accepted)
    /\ faultCount = Cardinality({c \in Connections : link[c].fault # "None"})
    /\ \A c \in Connections :
          /\ counts[c].replies <= counts[c].senderDebits
          /\ counts[c].senderDebits <= counts[c].writes
          /\ counts[c].replies <= counts[c].calls
          /\ counts[c].calls <= counts[c].admits
          /\ counts[c].admits <= counts[c].writes
          /\ counts[c].writes - counts[c].replies \in 0..1
          /\ counts[c].writes - counts[c].senderDebits =
                 (IF bpc[c] = "Debit" THEN 1 ELSE 0)
          /\ counts[c].admits - counts[c].calls =
                 (IF apc[c] = "Debited" THEN 1 ELSE 0)

ReceiverQuotaSafety == Accepted <= InitialQuota
BackendQuotaSafety == BackendCalls <= InitialQuota

\* CANDIDATE endpoint-accounting requirements, evaluated only after both
\* endpoints stop and all pending local debit/delivery steps are settled.
\* Not an assertion that instantaneous equality is meaningful or promised.
QuiescentAgreement == Terminated => senderRemaining = receiverRemaining
\* Same candidate goal restricted at QUERY time to an execution that already
\* received an ordinary reply. Next still permits failures at any round.
QuiescentAgreementAfterProgress ==
    (Terminated /\ Replies > 0) => senderRemaining = receiverRemaining
NoUnadmittedConsumption ==
    Terminated => (InitialQuota - senderRemaining) <= Accepted

\* Deliberately false witness queries: violation means this path is reachable.
NoResponseAbort == \A c \in Connections : link[c].fault # "ResponseAbort"
NoSendError == \A c \in Connections : link[c].fault # "SendError"

=============================================================================
