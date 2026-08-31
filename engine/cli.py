import argparse
import json
import sys
from dataclasses import asdict
from .models import TaskRecord, TaskState, ActorType
from .store import TaskStore
from .state_machine import TaskStateMachine
from .classifier.classifier import TaskClassifier
from .operators.registry import OperatorRegistry
from .operators.builtin.symbol_rename import SymbolRenameOperator
from .operators.builtin.file_move import FileMoveOperator
from .operators.context import OperatorContext
from .runtime.verifier import VerificationPlanner, VerificationRunner
from .runtime.sandbox.manager import SandboxManager
from .runtime.sandbox.models import SandboxSpec, SandboxMode, ExecutionTrustLevel, ExecutionCapability
from .runtime.sandbox.container_backend import ContainerSandboxBackend
from .runtime.sandbox.snapshot import WorkspaceSnapshotter
from .orchestrator.orchestrator import EngineeringOrchestrator
from .orchestrator.durability.store import DurableStore
from .orchestrator.durability.models import ReplayRequest, ReplayMode
from .orchestrator.durability.resume import WorkflowResumer
from .orchestrator.durability.replay import WorkflowReplayEngine
from .orchestrator.durability.recovery import WorkflowRecoveryManager
from repository.scan import RepositoryAnalyzer

def get_default_registry() -> OperatorRegistry:
    registry = OperatorRegistry()
    registry.register(SymbolRenameOperator())
    registry.register(FileMoveOperator())
    return registry

def main():
    parser = argparse.ArgumentParser(description="Mini-Jules Task Engine & Engineering Operator CLI")
    subparsers = parser.add_subparsers(dest="command", help="Subcommand to run")

    # task parser
    task_parser = subparsers.add_parser("task", help="Task management commands")
    task_sub = task_parser.add_subparsers(dest="task_command", help="Task action")

    # task create
    create_p = task_sub.add_parser("create", help="Create a new task record")
    create_p.add_argument("--root", required=True, help="Repository root path")
    create_p.add_argument("--request", required=True, help="Task request string")

    # task get
    get_p = task_sub.add_parser("get", help="Get a task record by ID")
    get_p.add_argument("task_id", help="Task ID")

    # task status / transition
    trans_p = task_sub.add_parser("transition", help="Transition task state")
    trans_p.add_argument("task_id", help="Task ID")
    trans_p.add_argument("target", help="Target TaskState enum value")
    trans_p.add_argument("--reason", required=True, help="Reason for transition")
    trans_p.add_argument("--actor", default="SYSTEM", help="Actor type (SYSTEM, USER, AGENT, RECOVERY)")

    # task list
    list_p = task_sub.add_parser("list", help="List tasks")
    list_p.add_argument("--status", help="Filter by TaskState enum value")

    # task events
    events_p = task_sub.add_parser("events", help="Get event audit history for a task")
    events_p.add_argument("task_id", help="Task ID")

    # task recover
    recover_p = task_sub.add_parser("recover", help="Recover interrupted tasks left in active states")

    # classify parser
    classify_p = subparsers.add_parser("classify", help="Deterministically classify an engineering request")
    classify_p.add_argument("request", help="Natural language request string")
    classify_p.add_argument("--root", help="Optional repository root path for context-aware classification")

    # plan parser
    plan_p = subparsers.add_parser("plan", help="Generate deterministic execution plan (non-mutating)")
    plan_p.add_argument("request", help="Request string")
    plan_p.add_argument("--root", default=".", help="Repository root path")

    # propose parser
    propose_p = subparsers.add_parser("propose", help="Generate dry-run proposal and diffs (non-mutating)")
    propose_p.add_argument("request", help="Request string")
    propose_p.add_argument("--root", default=".", help="Repository root path")

    # apply parser
    apply_p = subparsers.add_parser("apply", help="Apply proposed engineering changes (requires --approved)")
    apply_p.add_argument("request", help="Request string")
    apply_p.add_argument("--root", default=".", help="Repository root path")
    apply_p.add_argument("--approved", action="store_true", help="Explicit human approval flag")

    # verify-plan parser
    vplan_p = subparsers.add_parser("verify-plan", help="Inspect verification plan for request (non-executing)")
    vplan_p.add_argument("request", help="Request string")
    vplan_p.add_argument("--root", default=".", help="Repository root path")

    # verify parser
    verify_p = subparsers.add_parser("verify", help="Apply proposal and run controlled verification pipeline")
    verify_p.add_argument("request", help="Request string")
    verify_p.add_argument("--root", default=".", help="Repository root path")
    verify_p.add_argument("--approved", action="store_true", help="Explicit human approval flag for mutations and high-risk tests")

    # sandbox info parser
    sb_info_p = subparsers.add_parser("sandbox-info", help="Display sandbox capability & Docker detection metadata")
    sb_info_p.add_argument("--root", default=".", help="Repository root path")

    # sandbox execute parser
    sb_exec_p = subparsers.add_parser("sandbox-execute", help="Execute command inside sandbox environment")
    sb_exec_p.add_argument("command_name", help="Registered command name")
    sb_exec_p.add_argument("args", nargs="*", help="Extra arguments")
    sb_exec_p.add_argument("--mode", default="RESTRICTED_LOCAL", help="STATIC_ONLY, RESTRICTED_LOCAL, or ISOLATED")
    sb_exec_p.add_argument("--root", default=".", help="Repository root path")

    # sandbox snapshot parser
    sb_snap_p = subparsers.add_parser("sandbox-snapshot", help="Capture workspace snapshot and hash summary")
    sb_snap_p.add_argument("--root", default=".", help="Repository root path")

    # orchestrate parser
    orch_p = subparsers.add_parser("orchestrate", help="Run full deterministic engineering pipeline")
    orch_p.add_argument("request", help="Request string")
    orch_p.add_argument("--root", default=".", help="Repository root path")
    orch_p.add_argument("--approved", action="store_true", help="Explicit human approval flag")

    # workflow parser
    wf_p = subparsers.add_parser("workflow", help="Durable workflow management commands")
    wf_sub = wf_p.add_subparsers(dest="wf_command", help="Workflow action")

    wf_status_p = wf_sub.add_parser("status", help="Get workflow execution status")
    wf_status_p.add_argument("workflow_id", help="Workflow ID")

    wf_chks_p = wf_sub.add_parser("checkpoints", help="List workflow checkpoints")
    wf_chks_p.add_argument("workflow_id", help="Workflow ID")

    wf_events_p = wf_sub.add_parser("events", help="List workflow event log")
    wf_events_p.add_argument("workflow_id", help="Workflow ID")

    wf_resume_p = wf_sub.add_parser("resume", help="Resume interrupted workflow")
    wf_resume_p.add_argument("workflow_id", help="Workflow ID")
    wf_resume_p.add_argument("--root", default=".", help="Repository root path")

    wf_replay_p = wf_sub.add_parser("replay", help="Deterministically replay workflow")
    wf_replay_p.add_argument("workflow_id", help="Workflow ID")
    wf_replay_p.add_argument("--mode", default="DRY_RUN", help="DRY_RUN, VALIDATION_ONLY, or FULL_REPLAY")

    args = parser.parse_args()

    store = TaskStore()
    sm = TaskStateMachine(store)
    classifier = TaskClassifier()
    registry = get_default_registry()
    vplanner = VerificationPlanner()
    vrunner = VerificationRunner(state_machine=sm)
    sb_manager = SandboxManager()

    if args.command == "sandbox-info":
        docker_status = ContainerSandboxBackend.detect_docker_availability()
        info = {
            "docker_availability": docker_status,
            "supported_modes": [m.value for m in SandboxMode],
            "capabilities": [c.value for c in ExecutionCapability],
            "trust_levels": [t.value for t in ExecutionTrustLevel],
            "repository_root": args.root
        }
        print(json.dumps(info, indent=2))

    elif args.command == "orchestrate":
        orchestrator = EngineeringOrchestrator(store=store, registry=registry, sandbox_manager=sb_manager)
        report = orchestrator.run(repository_root=args.root, request_string=args.request, approved=args.approved)
        print(json.dumps(asdict(report), indent=2))

    elif args.command == "workflow":
        durable_store = DurableStore()
        if args.wf_command == "status":
            wf = durable_store.get_workflow(args.workflow_id)
            if not wf:
                print(json.dumps({"error": f"Workflow {args.workflow_id} not found"}, indent=2))
                sys.exit(1)
            print(json.dumps(asdict(wf), indent=2))

        elif args.wf_command == "checkpoints":
            chks = durable_store.list_checkpoints(args.workflow_id)
            print(json.dumps([asdict(c) for c in chks], indent=2))

        elif args.wf_command == "events":
            evts = durable_store.list_events(args.workflow_id)
            print(json.dumps([asdict(e) for e in evts], indent=2))

        elif args.wf_command == "resume":
            resumer = WorkflowResumer(durable_store)
            snap = WorkspaceSnapshotter.capture(args.root)
            try:
                res = resumer.resume_workflow(args.workflow_id, snap.summary_hash)
                print(json.dumps(res, indent=2))
            except Exception as e:
                print(json.dumps({"error": str(e)}, indent=2))
                sys.exit(1)

        elif args.wf_command == "replay":
            replay_eng = WorkflowReplayEngine(durable_store)
            snap = WorkspaceSnapshotter.capture(".")
            req = ReplayRequest(
                source_workflow_id=args.workflow_id,
                requested_by="CLI",
                replay_mode=ReplayMode(args.mode.upper()),
                expected_workspace_fingerprint=snap.summary_hash
            )
            try:
                res = replay_eng.replay_workflow(req)
                print(json.dumps(res, indent=2))
            except Exception as e:
                print(json.dumps({"error": str(e)}, indent=2))
                sys.exit(1)

        else:
            wf_p.print_help()

    elif args.command == "sandbox-snapshot":
        snap = WorkspaceSnapshotter.capture(args.root)
        summary = {
            "workspace_root": snap.workspace_root,
            "file_count": len(snap.files),
            "summary_hash": snap.summary_hash
        }
        print(json.dumps(summary, indent=2))

    elif args.command == "sandbox-execute":
        mode_enum = SandboxMode(args.mode.upper())
        spec = SandboxSpec(
            sandbox_id="CLI-SB-EXEC",
            mode=mode_enum,
            workspace_root=args.root,
            allowed_capabilities={ExecutionCapability.STATIC_ANALYSIS, ExecutionCapability.READ_WORKSPACE, ExecutionCapability.EXECUTE_COMMAND, ExecutionCapability.RUN_TESTS},
            trust_level=ExecutionTrustLevel.UNTRUSTED_REPOSITORY_CODE if mode_enum != SandboxMode.STATIC_ONLY else ExecutionTrustLevel.NO_CODE_EXECUTION
        )
        try:
            res = sb_manager.execute_in_sandbox(spec, args.command_name, args.args)
            print(json.dumps(asdict(res), indent=2))
        except Exception as e:
            print(json.dumps({"error": str(e)}, indent=2))
            sys.exit(1)

    elif args.command == "classify":
        repo_snapshot = RepositoryAnalyzer.analyze(args.root) if args.root else None
        res = classifier.classify(args.request, repo_snapshot)
        print(json.dumps(asdict(res), indent=2))

    elif args.command == "plan":
        repo_snapshot = RepositoryAnalyzer.analyze(args.root)
        classification = classifier.classify(args.request, repo_snapshot)
        op = registry.get_operator_for_task(classification.task_type)
        if not op:
            print(json.dumps({"error": f"No operator found for task type {classification.task_type}"}, indent=2))
            sys.exit(1)

        ctx = OperatorContext(repository_root=args.root, task_id="CLI-PLAN", classification=classification, repo_snapshot=repo_snapshot)
        plan_res = op.plan(ctx)
        print(json.dumps(asdict(plan_res), indent=2))

    elif args.command == "propose":
        repo_snapshot = RepositoryAnalyzer.analyze(args.root)
        classification = classifier.classify(args.request, repo_snapshot)
        op = registry.get_operator_for_task(classification.task_type)
        if not op:
            print(json.dumps({"error": f"No operator found for task type {classification.task_type}"}, indent=2))
            sys.exit(1)

        ctx = OperatorContext(repository_root=args.root, task_id="CLI-PROPOSE", classification=classification, repo_snapshot=repo_snapshot)
        plan_res = op.plan(ctx)
        proposal = op.propose(ctx, plan_res)
        print(json.dumps(asdict(proposal), indent=2))

    elif args.command == "apply":
        repo_snapshot = RepositoryAnalyzer.analyze(args.root)
        classification = classifier.classify(args.request, repo_snapshot)
        op = registry.get_operator_for_task(classification.task_type)
        if not op:
            print(json.dumps({"error": f"No operator found for task type {classification.task_type}"}, indent=2))
            sys.exit(1)

        ctx = OperatorContext(repository_root=args.root, task_id="CLI-APPLY", classification=classification, repo_snapshot=repo_snapshot)
        plan_res = op.plan(ctx)
        proposal = op.propose(ctx, plan_res)

        try:
            apply_res = op.apply(ctx, proposal, approved=args.approved)
            print(json.dumps(asdict(apply_res), indent=2))
        except Exception as e:
            print(json.dumps({"error": str(e)}, indent=2))
            sys.exit(1)

    elif args.command == "verify-plan":
        repo_snapshot = RepositoryAnalyzer.analyze(args.root)
        classification = classifier.classify(args.request, repo_snapshot)
        op = registry.get_operator_for_task(classification.task_type)
        if not op:
            print(json.dumps({"error": f"No operator found for task type {classification.task_type}"}, indent=2))
            sys.exit(1)

        ctx = OperatorContext(repository_root=args.root, task_id="CLI-VPLAN", classification=classification, repo_snapshot=repo_snapshot)
        plan_res = op.plan(ctx)
        proposal = op.propose(ctx, plan_res)
        vplan = vplanner.build_plan(ctx.task_id, proposal, repo_snapshot)
        print(json.dumps(asdict(vplan), indent=2))

    elif args.command == "verify":
        repo_snapshot = RepositoryAnalyzer.analyze(args.root)
        classification = classifier.classify(args.request, repo_snapshot)
        op = registry.get_operator_for_task(classification.task_type)
        if not op:
            print(json.dumps({"error": f"No operator found for task type {classification.task_type}"}, indent=2))
            sys.exit(1)

        # Create persistent task record
        record = store.create_task(TaskRecord(
            task_id="",
            repository_root=args.root,
            request=args.request,
            status=TaskState.RECEIVED
        ))
        ctx = OperatorContext(repository_root=args.root, task_id=record.task_id, classification=classification, repo_snapshot=repo_snapshot)
        plan_res = op.plan(ctx)
        proposal = op.propose(ctx, plan_res)

        try:
            apply_res = op.apply(ctx, proposal, approved=args.approved)
            if not apply_res.success:
                print(json.dumps({"error": f"Apply failed: {apply_res.error}"}, indent=2))
                sys.exit(1)

            vplan = vplanner.build_plan(ctx.task_id, proposal, repo_snapshot)
            vres = vrunner.run_verification(
                context=ctx,
                proposal=proposal,
                operator=op,
                plan=vplan,
                execution_approved=args.approved
            )
            print(json.dumps(asdict(vres), indent=2))
        except Exception as e:
            print(json.dumps({"error": str(e)}, indent=2))
            sys.exit(1)

    elif args.command == "task":
        if args.task_command == "create":
            record = TaskRecord(
                task_id=store.generate_task_id(),
                repository_root=args.root,
                request=args.request,
                status=TaskState.RECEIVED
            )
            created = store.create_task(record)
            print(json.dumps(asdict(created), indent=2))

        elif args.task_command == "get":
            task = store.get_task(args.task_id)
            if not task:
                print(json.dumps({"error": f"Task {args.task_id} not found"}, indent=2))
                sys.exit(1)
            print(json.dumps(asdict(task), indent=2))

        elif args.task_command == "transition":
            try:
                target_state = TaskState(args.target.upper())
                actor = ActorType(args.actor.upper())
                updated = sm.transition(
                    task_id=args.task_id,
                    target_state=target_state,
                    reason=args.reason,
                    actor=actor
                )
                print(json.dumps(asdict(updated), indent=2))
            except Exception as e:
                print(json.dumps({"error": str(e)}, indent=2))
                sys.exit(1)

        elif args.task_command == "list":
            status_enum = TaskState(args.status.upper()) if args.status else None
            tasks = store.list_tasks(status=status_enum)
            print(json.dumps([asdict(t) for t in tasks], indent=2))

        elif args.task_command == "events":
            evts = store.get_task_events(args.task_id)
            print(json.dumps([asdict(e) for e in evts], indent=2))

        elif args.task_command == "recover":
            recovered = sm.recover_interrupted_tasks()
            print(json.dumps([asdict(t) for t in recovered], indent=2))

        else:
            task_parser.print_help()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
