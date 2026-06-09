"""Build-Step-Modell für ViUR-Projekte.

Reiner, conf-freier Kern: Jeder Eintrag aus dem ``builds``-Abschnitt eines
Profils wird über :func:`from_config` zu einer :class:`BuildStep`-Instanz. Der
Kommando-Aufbau (:meth:`BuildStep.build_command`), die Env-Auflösung
(:meth:`BuildStep.resolve_env`) und das Arbeitsverzeichnis
(:meth:`BuildStep.resolve_cwd`) sind seiteneffektfrei und damit unit-testbar;
nur :meth:`BuildStep.run` / :meth:`BuildStep.clean` führen tatsächlich etwas aus.

Bewusst KEIN Import aus ``.conf`` — dieses Modul bekommt das aufgelöste Profil
als ``conf``-dict übergeben. Würde ``conf`` importiert, löste das beim Import die
``project.json``-Suche samt ``os.chdir`` aus (s. Modul-Singleton in ``conf.py``).
"""

import os
import shlex
import typing as t
from dataclasses import dataclass, field
from pathlib import Path

from . import utils


def _expansion_vars(conf: dict) -> dict[str, str]:
    """Die für `$(…)`-Expansion in env-Werten nutzbaren String-Felder des Profils."""
    return {key: value for key, value in conf.items() if isinstance(value, str)}


@dataclass(frozen=True, slots=True, kw_only=True)
class BuildStep:
    """Ein einzelner Build-Schritt aus dem ``builds``-Abschnitt eines Profils.

    Attributes:
        name: Schlüssel des Eintrags (nur für Log-Ausgaben).
        command: Bei ``npm`` der npm-Script-Name, bei ``exec`` ein Shell-String.
        version: Reines Metadatum (z.B. von ``viur env`` angezeigt); fließt
            NICHT in das Build-Kommando ein.
        clean_cmd: Optionaler Shell-Befehl, der beim ``clean`` zusätzlich läuft.
        args: Statische Zusatzargumente aus der Config; werden den
            CLI-Pass-through-Args vorangestellt.
        env: Statische Environment-Variablen aus der Config. Werte unterstützen
            ``$(…)``-Expansion.
    """

    kind: t.ClassVar[str] = "build"

    name: str
    command: str
    version: str | None = None
    clean_cmd: str | None = None
    args: tuple[str, ...] = ()
    env: dict[str, str] = field(default_factory=dict)

    def build_command(self, conf: dict, extra_args: t.Sequence[str]) -> str:
        """Baue die auszuführende Befehlszeichenkette (ohne sie auszuführen)."""
        raise NotImplementedError

    def resolve_cwd(self, conf: dict) -> Path | None:
        """Arbeitsverzeichnis für die Ausführung (``None`` = Projektroot)."""
        return None

    def resolve_env(self, conf: dict, extra_env: dict[str, str]) -> dict[str, str]:
        """Env-Overrides für diesen Schritt (Config-env, von CLI-env überschrieben).

        Gibt ausschließlich die Overrides zurück — NICHT ``os.environ``. Jeder
        Wert wird via :func:`utils.replace_vars` expandiert (pro Wert mit einer
        Wegwerf-Kopie der Variablen, da ``replace_vars`` sein Argument mutiert).
        """
        if not (overrides := {**self.env, **extra_env}):
            return {}

        variables = _expansion_vars(conf)
        return {key: utils.replace_vars(value, dict(variables)) for key, value in overrides.items()}

    def run(
        self,
        conf: dict,
        *,
        extra_args: t.Sequence[str] = (),
        extra_env: dict[str, str] | None = None,
        verbose: bool = False,
    ) -> None:
        """Führe den Build-Schritt aus."""
        cmd = self.build_command(conf, extra_args)
        overrides = self.resolve_env(conf, extra_env or {})
        cwd = self.resolve_cwd(conf)

        if verbose:
            utils.echo_info(f"  $ {cmd}")
            if cwd is not None:
                utils.echo_info(f"    (cwd: {cwd})")
            for key, value in overrides.items():
                utils.echo_info(f"    env: {key}={value}")

        # Aufrufer liefert vollständig: os.environ + Overrides. Ohne Overrides
        # erbt der Subprozess die Umgebung wie bisher (env=None).
        env = {**os.environ, **overrides} if overrides else None
        utils.system(cmd, cwd=cwd, env=env)

    def clean(self, conf: dict, *, verbose: bool = False) -> None:
        """Entferne erzeugte Artefakte. Basis: nur der optionale ``clean_cmd``."""
        if self.clean_cmd:
            if verbose:
                utils.echo_info(f"  $ {self.clean_cmd}")
            utils.system(self.clean_cmd)


@dataclass(frozen=True, slots=True, kw_only=True)
class NpmBuildStep(BuildStep):
    """npm-Build: ``npm install && npm run <command>`` im Quellverzeichnis.

    Attributes:
        source: Pfad des npm-Projekts relativ zu ``conf['sources_folder']``.
        target: Ausgabe-Ordner relativ zu ``conf['distribution_folder']`` —
            nur für ``clean`` relevant.
    """

    kind: t.ClassVar[str] = "npm"

    source: str = ""
    target: str | None = None

    def build_command(self, conf: dict, extra_args: t.Sequence[str]) -> str:
        cmd = f"npm install && npm run {self.command}"
        # npm-Konvention: Script-Args stehen hinter `--`. Kein nacktes `--`,
        # wenn es keine Args gibt.
        if all_args := (*self.args, *extra_args):
            cmd += f" -- {shlex.join(all_args)}"
        return cmd

    def resolve_cwd(self, conf: dict) -> Path | None:
        return Path(conf["sources_folder"]) / self.source

    def clean(self, conf: dict, *, verbose: bool = False) -> None:
        if self.target:
            target_dir = Path(conf["distribution_folder"]) / self.target
            if verbose:
                utils.echo_info(f"  - dropping {target_dir}")
            utils.rmdir(str(target_dir))

        node_modules = Path(conf["sources_folder"]) / self.source / "node_modules"
        if verbose:
            utils.echo_info(f"  - dropping {node_modules}")
        utils.rmdir(str(node_modules))

        super().clean(conf, verbose=verbose)


@dataclass(frozen=True, slots=True, kw_only=True)
class ExecBuildStep(BuildStep):
    """exec-Build: ein roher Shell-Befehl, im Projektroot ausgeführt."""

    kind: t.ClassVar[str] = "exec"

    def build_command(self, conf: dict, extra_args: t.Sequence[str]) -> str:
        cmd = self.command
        # `command` bleibt roh-Shell; nur die Args werden gequotet.
        if all_args := (*self.args, *extra_args):
            cmd += f" {shlex.join(all_args)}"
        return cmd


def from_config(name: str, cfg: dict) -> BuildStep:
    """Erzeuge den passenden BuildStep aus einem ``builds``-Eintrag.

    Raises:
        ValueError: bei unbekanntem ``kind`` (die CLI-Schicht übersetzt das in
            ein ``echo_fatal``).
    """
    common: dict[str, t.Any] = {
        "name": name,
        "command": cfg["command"],
        "version": cfg.get("version"),
        "clean_cmd": cfg.get("clean"),
        "args": tuple(cfg.get("args", ())),
        "env": dict(cfg.get("env", {})),
    }
    match cfg["kind"]:
        case "npm":
            return NpmBuildStep(source=cfg.get("source", ""), target=cfg.get("target"), **common)
        case "exec":
            return ExecBuildStep(**common)
        case other:
            raise ValueError(f"Unbekannte build kind {other!r}")
