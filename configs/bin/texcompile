#!/usr/bin/env python3

import glob
import os
import os.path
import re
import shutil
import subprocess
import sys

class TeXCompiler(object):

    @classmethod
    def main(cls):
        if sys.argv[1] == "-f":
            file = sys.argv[2]
            compiler = cls(file, silent=True)
            compiler.parse_config()
            print(compiler.file_path)
            target_file = os.path.join(
                os.path.dirname(compiler.file_path),
                compiler.job_name + "." + compiler.tex_mode)
            print(target_file)
        else:
            file = sys.argv[1]
            compiler = cls(file)
            has_errors = compiler.run()
            if has_errors:
                sys.exit(1)

    def __init__(self, file, silent=False):
        self.file = file
        self.silent = silent
        self.verbose = False

    def set_defaults(self):
        ext = os.path.splitext(self.file)[1]
        if ext != ".tex":
            file_guess = self.file + ".tex"
            if os.path.exists(file_guess):
                self.file = file_guess
            else:
                for file_guess in sorted(glob.glob(self.file + "*.tex")):
                    self.file = file_guess
                    break
        self.file_path = os.path.abspath(self.file)
        self.file_fullname = os.path.basename(self.file_path)
        self.file_name, self.file_ext = os.path.splitext(self.file_fullname)
        self.job_name = self.file_name
        self.file_dir = os.path.dirname(self.file_path)
        self.tex_command = "pdflatex"
        self.tex_mode = "pdf"
        self.tex_engine_name = "pdfLaTeX"
        self.tex_extra_options = []
        self.use_make = False
        self.use_synctex = True
        self.use_bib = False
        self.use_aux_dir = False
        self.make_target = None
        self.bib_command = None
        self.bib_engine_name = None
        self.bib_file = None
        self.aux_dir = None

    def parse_config(self):
        self.set_defaults()
        os.chdir(self.file_dir)
        with open(self.file_fullname) as tex_file:
            for line in tex_file:
                if not self.parse_config_line(line):
                    break

    config_line_re = re.compile(r"^\s*%+\s*texcompile\s*:\s*(\S+)\s*(.*)",re.I)

    def parse_config_line(self, line):

        match = self.config_line_re.match(line)
        if match:

            option, arg = match.groups()

            if option in ["main", "mainfile", "main_file", "main-file"]:
                self.file = arg
                if not self.silent:
                    print("Using main project file `%s`" % self.file)
                self.parse_config()
                return False

            elif option == "verbose":
                if not self.silent:
                    print("Verbose output on")
                self.verbose = True

            elif option == "make":
                self.use_make = True
                self.make_target = arg

            elif option in ["dvi", "latex"]:
                self.tex_command = "latex"
                self.tex_mode = "dvi"
                self.tex_engine_name = "LaTeX"
            elif option in ["pdf", "pdflatex"]:
                self.tex_command = "pdflatex"
                self.tex_mode = "pdf"
                self.tex_engine_name = "pdfLaTeX"
            elif option == "xelatex":
                self.tex_command = "xelatex"
                self.tex_mode = "pdf"
                self.tex_engine_name = "XeLaTeX"
            elif option == "lualatex":
                self.tex_command = "lualatex"
                self.tex_mode = "pdf"
                self.tex_engine_name = "LuaLaTeX"

            elif option == "tex":
                self.tex_command = "tex"
                self.tex_mode = "dvi"
                self.tex_engine_name = "TeX"
            elif option == "pdftex":
                self.tex_command = "pdftex"
                self.tex_mode = "pdf"
                self.tex_engine_name = "pdfTeX"
            elif option == "xetex":
                self.tex_command = "xetex"
                self.tex_mode = "pdf"
                self.tex_engine_name = "XeTeX"
            elif option == "luatex":
                self.tex_command = "luatex"
                self.tex_mode = "pdf"
                self.tex_engine_name = "LuaTeX"

            elif option == "synctex":
                if arg in ["", "on", "yes", "true"]:
                    self.use_synctex = True
                elif arg in ["off", "no", "false"]:
                    self.use_synctex = False

            elif option in ["jobname", "job-name"]:
                self.tex_extra_options.append("-jobname=" + arg)
                self.job_name = arg

            elif option in ["options", "args", "arguments", "extraoptions",
                            "extra_options", "extra-options"]:
                self.tex_extra_options += arg.split()
                for extra_option in self.tex_extra_options:
                    if "=" in extra_option:
                        eo_head, eo_tail = extra_option.split("=")
                        if eo_head == "-jobname":
                            self.job_name = eo_tail

            elif option == "bibtex":
                self.use_bib = True
                self.bib_command = "bibtex"
                self.bib_engine_name = "BibTeX"
            elif option == "biber":
                self.use_bib = True
                self.bib_command = "biber"
                self.bib_engine_name = "Biber"
            elif option in ["bibtexfile", "bibtex-file", "bibtex_file",
                            "bibfile", "bib-file", "bib_file"]:
                self.bib_file = arg
                if not self.use_bib:
                    self.use_bib = True
                    self.bib_command = "bibtex"
                    self.bib_engine_name = "BibTeX"

            elif option in ["auxdir", "aux_dir", "aux-dir"]:
                self.use_aux_dir = True
                if arg:
                    self.aux_dir = arg
                else:
                    self.aux_dir = "tex_aux"

        return True

    def set_tex_options(self):
        self.tex_options = ["-interaction=nonstopmode"]
        self.aux_file = self.job_name + ".aux"
        self.bbl_file = self.job_name + ".bbl"
        self.log_file = self.job_name + ".log"
        if self.tex_mode != "pdf":
            self.use_synctex = False
        if self.use_synctex:
            self.tex_options.append("-synctex=1")
        self.full_tex_command = (
            [self.tex_command] + self.tex_options + 
            self.tex_extra_options + [self.file_name])

    def run(self):
        print("="*70)
        print("TeXCompile")
        print("-"*70)
        print("Using file `%s`" % self.file)
        self.parse_config()
        self.set_tex_options()
        if self.use_aux_dir:
            print("Using aux directory `%s`" % self.aux_dir)
        if self.use_make:
            self.run_make()
        else:
            if self.verbose and self.use_synctex:
                print("Using SyncTeX")
            self.run_tex()
        has_errors = self.print_errors()
        print("="*70)
        return has_errors

    def run_tex(self):
        if self.verbose:
            tcmd = " ".join(self.full_tex_command)
            print("The full TeX command is\n$ %s" % tcmd)
        if self.use_aux_dir:
            if os.path.exists(self.aux_dir):
                if not os.path.isdir(self.aux_dir):
                    print("%s: Error. Cannot use aux-dir ($s)" % (self.file,
                                                                  self.aux_dir)) 
                    return
            else:
                os.mkdir(self.aux_dir)
            self.move_files_from_aux_dir()
        error_ocurred = False
        run_count = 0
        needs_rerun = True
        while needs_rerun and run_count <= 5:
            needs_rerun = False
            run_count += 1
            if run_count == 1:
                print("Running %s" % self.tex_engine_name)
                sys.stdout.flush()
            else:
                print("Running %s (pass %s)" % (self.tex_engine_name,
                                                run_count))
                sys.stdout.flush()
            tex_proc = subprocess.Popen(
                self.full_tex_command,
                stdout = subprocess.PIPE,
                stderr = subprocess.STDOUT)
            tex_retcode = tex_proc.wait()
            if tex_retcode != 0:
                if self.verbose:
                    print(("Error occurred when running %s" %
                           self.tex_engine_name))
                error_ocurred = True
                break
            needs_rerun, needs_bib = self.parse_log_file()
            if not needs_bib and self.bib_file is not None:
                if (os.path.exists(self.bib_file) and
                        os.path.exists(self.bbl_file)):
                    bib_time = os.path.getmtime(self.bib_file)
                    bbl_time = os.path.getmtime(self.bbl_file)
                    if bib_time > bbl_time:
                        needs_bib = True
            if (self.verbose and self.use_bib 
                    and run_count==1 and not needs_bib):
                print("No need to run %s" % self.bib_engine_name)
            if needs_bib and self.use_bib and run_count==1:
                print("Running %s" % self.bib_engine_name)
                sys.stdout.flush()
                full_bib_command = [self.bib_command, self.job_name]
                if os.path.exists(self.bbl_file):
                    with open(self.bbl_file) as bbl_file:
                        prev_bbl = bbl_file.read()
                else:
                    prev_bbl = ""
                bib_proc = subprocess.Popen(
                    full_bib_command,
                    stdout = subprocess.PIPE,
                    stderr = subprocess.STDOUT)
                bib_retcode = bib_proc.wait()
                if bib_retcode != 0:
                    if self.verbose:
                        print(("Error occurred when running %s" %
                               self.bib_engine_name))
                    error_ocurred = True
                    break
                if os.path.exists(self.bbl_file):
                    with open(self.bbl_file) as bbl_file:
                        new_bbl = bbl_file.read()
                else:
                    new_bbl = ""
                if prev_bbl != new_bbl:
                    needs_rerun = True
                elif self.verbose:
                    print(("No need to rerun %s, bbl file did not change." %
                           self.tex_engine_name))
        if self.use_aux_dir:
            self.move_files_to_aux_dir()

    def parse_log_file(self):
        if self.verbose:
            print("Processing log file `%s`" % self.log_file)
        needs_rerun = False
        needs_bib = False
        with open(self.log_file, encoding='latin1') as log_file:
            for line in log_file:
                if "Rerun to get cross-references right" in line:
                    needs_rerun = True
                if "There were undefined references" in line:
                    needs_bib = True
        if self.verbose:
            if needs_rerun:
                print("Found `Rerun to get cross-references right`")
            if needs_bib:
                print("Found `There were undefined references`")
        return needs_rerun, needs_bib

    def move_aux_files(self, direction):
        aux_extensions = [".aux", ".log", ".toc", ".bbl", ".brf", ".out",
                          ".blg", ".nav", ".snm", ".vrb", ".bcf", ".run.xml",
                          ".spl"] # ".synctex.gz"
        for ext in aux_extensions:
            file1 = self.job_name + ext
            file2 = os.path.join(self.aux_dir, file1)
            if direction == "to_aux_dir":
                if os.path.exists(file1):
                    if self.verbose:
                        print("Moving `%s` to `%s`" %(file1,file2))
                    os.rename(file1, file2)
            elif direction == "from_aux_dir":
                if not os.path.exists(file1):
                    if os.path.exists(file2):
                        if self.verbose:
                            print("Moving `%s` to `%s`" %(file2,file1))
                        os.rename(file2, file1)

    def move_files_to_aux_dir(self):
        if self.verbose:
            print("Moving files to aux dir")
        self.move_aux_files("to_aux_dir")

    def move_files_from_aux_dir(self):
        if self.verbose:
            print("Moving files from aux dir")
        self.move_aux_files("from_aux_dir")

    def run_make(self):
        if self.make_target:
            print("Running Makefile (target `%s`)" % self.make_target)
            sys.stdout.flush()
            make_command = ["make", self.make_target]
        else:
            print("Running Makefile (no target specified, using default)")
            sys.stdout.flush()
            make_command = ["make"]
        make_proc = subprocess.Popen(make_command)
        make_retcode = make_proc.wait()

    def print_errors(self):
        log = LogCheck()
        log_file = self.log_file
        if self.run_tex and self.use_aux_dir:
            log_file = os.path.join(self.aux_dir, log_file)
        log.read(log_file)
        has_errors = False
        for i,error in enumerate(log.get_errors()):
            if i==0:
                print("-"*70)
            self.print_one_error(error)
            has_errors = True
        return has_errors

    def print_one_error(self, error):
        where = error
        if "text" in error:
            text = error["text"]
        else:
            text = ""
        if "file" in where and where["file"] is not None:
            pos = self.simplify_path(where["file"])
            if "line" in where and where["line"]:
                pos = "%s:%d" % (pos, int(where["line"]))
                if "last" in where:
                    if where["last"] != where["line"]:
                        pos = "%s-%d" % (pos, int(where["last"]))
            pos = pos + ": "
        else:
            pos = ""
        if "macro" in where:
            text = "%s (in macro %s)" % (text, where["macro"])
        if "page" in where:
            text = "%s (page %d)" % (text, int(where["page"]))
        if "pkg" in where:
            text = "[%s] %s" % (where["pkg"], text)
        print(pos + text)
        sys.stdout.flush()

    def simplify_path(self, name):
        return name
        # path = os.path.normpath(os.path.join(self.file_dir, name))
        # if path[:len(self.cwd)] == self.cwd:
        #     return path[len(self.cwd):]
        # return path

########################################################################
#
# RUBBER_INFO
#
# The code below was shamefully copied from rubber:
#
#   https://launchpad.net/rubber
#
# Rubber is licensed under GPL
#
########################################################################

re_loghead = re.compile("This is [0-9a-zA-Z-]*(TeX|Omega)")
re_rerun = re.compile("LaTeX Warning:.*Rerun")
re_file = re.compile("(\\((?P<file>[^ \n\t(){}]*)|\\))")
re_badbox = re.compile(r"(Ov|Und)erfull \\[hv]box ")
re_line = re.compile(r"(l\.(?P<line>[0-9]+)( (?P<code>.*))?$|<\*>)")
re_cseq = re.compile(r".*(?P<seq>(\\|\.\.\.)[^ ]*) ?$")
re_macro = re.compile(r"^(?P<macro>\\.*) ->")
re_page = re.compile("\[(?P<num>[0-9]+)\]")
re_atline = re.compile(
"( detected| in paragraph)? at lines? (?P<line>[0-9]*)(--(?P<last>[0-9]*))?")
re_reference = re.compile("LaTeX Warning: Reference `(?P<ref>.*)' \
on page (?P<page>[0-9]*) undefined on input line (?P<line>[0-9]*)\\.$")
re_label = re.compile("LaTeX Warning: (?P<text>Label .*)$")
re_warning = re.compile(
"(LaTeX|Package)( (?P<pkg>.*))? Warning: (?P<text>.*)$")
re_online = re.compile("(; reported)? on input line (?P<line>[0-9]*)")
re_ignored = re.compile("; all text was ignored after line (?P<line>[0-9]*).$")

class LogCheck (object):
    """
    This class performs all the extraction of information from the log file.
    For efficiency, the instances contain the whole file as a list of strings
    so that it can be read several times with no disk access.
    """
    #-- Initialization {{{2

    def __init__ (self):
        self.lines = None

    def read (self, name):
        """
        Read the specified log file, checking that it was produced by the
        right compiler. Returns true if the log file is invalid or does not
        exist.
        """
        self.lines = None
        try:
            file = open(name, encoding="latin1")
        except IOError:
            return 2
        line = file.readline()
        if not line:
            file.close()
            return 1
        if not re_loghead.match(line):
            file.close()
            return 1
        self.lines = file.readlines()
        file.close()
        return 0

    #-- Process information {{{2

    def errors (self):
        """
        Returns true if there was an error during the compilation.
        """
        skipping = 0
        for line in self.lines:
            if line.strip() == "":
                skipping = 0
                continue
            if skipping:
                continue
            m = re_badbox.match(line)
            if m:
                skipping = 1
                continue
            if line[0] == "!":
                # We check for the substring "pdfTeX warning" because pdfTeX
                # sometimes issues warnings (like undefined references) in the
                # form of errors...

                if line.find("pdfTeX warning") == -1:
                    return 1
        return 0

    def run_needed (self):
        """
        Returns true if LaTeX indicated that another compilation is needed.
        """
        for line in self.lines:
            if re_rerun.match(line):
                return 1
        return 0

    #-- Information extraction {{{2

    def continued (self, line):
        """
        Check if a line in the log is continued on the next line. This is
        needed because TeX breaks messages at 79 characters per line. We make
        this into a method because the test is slightly different in Metapost.
        """
        return len(line) == 79

    def parse (self, errors=0, boxes=0, refs=0, warnings=0):
        """
        Parse the log file for relevant information. The named arguments are
        booleans that indicate which information should be extracted:
        - errors: all errors
        - boxes: bad boxes
        - refs: warnings about references
        - warnings: all other warnings
        The function returns a generator. Each generated item is a dictionary
        that contains (some of) the following entries:
        - kind: the kind of information ("error", "box", "ref", "warning")
        - text: the text of the error or warning
        - code: the piece of code that caused an error
        - file, line, last, pkg: as used by Message.format_pos.
        """
        if not self.lines:
            return
        last_file = None
        pos = [last_file]
        page = 1
        parsing = 0    # 1 if we are parsing an error's text
        skipping = 0   # 1 if we are skipping text until an empty line
        something = 0  # 1 if some error was found
        prefix = None  # the prefix for warning messages from packages
        accu = ""      # accumulated text from the previous line
        macro = None   # the macro in which the error occurs
        cseqs = {}     # undefined control sequences so far
        for line in self.lines:
            line = line[:-1]  # remove the line feed

            # TeX breaks messages at 79 characters, just to make parsing
            # trickier...

            if not parsing and self.continued(line):
                accu += line
                continue
            line = accu + line
            accu = ""

            # Text that should be skipped (from bad box messages)

            if prefix is None and line == "":
                skipping = 0
                continue

            if skipping:
                continue

            # Errors (including aborted compilation)

            if parsing:
                if error == "Undefined control sequence.":
                    # This is a special case in order to report which control
                    # sequence is undefined.
                    m = re_cseq.match(line)
                    if m:
                        seq = m.group("seq")
                        if seq in cseqs:
                            error = None
                        else:
                            cseqs[seq] = None
                            error = "Undefined control sequence %s." % m.group("seq")
                m = re_macro.match(line)
                if m:
                    macro = m.group("macro")
                m = re_line.match(line)
                if m:
                    parsing = 0
                    skipping = 1
                    pdfTeX = line.find("pdfTeX warning") != -1
                    if error is not None and ((pdfTeX and warnings) or (errors and not pdfTeX)):
                        if pdfTeX:
                            d = {
                                "kind": "warning",
                                "pkg": "pdfTeX",
                                "text": error[error.find(":")+2:]
                            }
                        else:
                            d = {
                                "kind": "error",
                                "text": error
                            }
                        d.update( m.groupdict() )
                        m = re_ignored.search(error)
                        if m:
                            d["file"] = last_file
                            if "code" in d:
                                del d["code"]
                            d.update( m.groupdict() )
                        elif pos[-1] is None:
                            d["file"] = last_file
                        else:
                            d["file"] = pos[-1]
                        if macro is not None:
                            d["macro"] = macro
                            macro = None
                        yield d
                elif line[0] == "!":
                    error = line[2:]
                elif line[0:3] == "***":
                    parsing = 0
                    skipping = 1
                    if errors:
                        yield   {
                            "kind": "abort",
                            "text": error,
                            "why" : line[4:],
                            "file": last_file
                            }
                elif line[0:15] == "Type X to quit ":
                    parsing = 0
                    skipping = 0
                    if errors:
                        yield   {
                            "kind": "error",
                            "text": error,
                            "file": pos[-1]
                            }
                continue

            if len(line) > 0 and line[0] == "!":
                error = line[2:]
                parsing = 1
                continue

            if line == "Runaway argument?":
                error = line
                parsing = 1
                continue

            # Long warnings

            if prefix is not None:
                if line[:len(prefix)] == prefix:
                    text.append(line[len(prefix):].strip())
                else:
                    text = " ".join(text)
                    m = re_online.search(text)
                    if m:
                        info["line"] = m.group("line")
                        text = text[:m.start()] + text[m.end():]
                    if warnings:
                        info["text"] = text
                        d = { "kind": "warning" }
                        d.update( info )
                        yield d
                    prefix = None
                continue

            # Undefined references

            m = re_reference.match(line)
            if m:
                if refs:
                    d = {
                        "kind": "warning",
                        "text": _("Reference `%s' undefined.") % m.group("ref"),
                        "file": pos[-1]
                        }
                    d.update( m.groupdict() )
                    yield d
                continue

            m = re_label.match(line)
            if m:
                if refs:
                    d = {
                        "kind": "warning",
                        "file": pos[-1]
                        }
                    d.update( m.groupdict() )
                    yield d
                continue

            # Other warnings

            if line.find("Warning") != -1:
                m = re_warning.match(line)
                if m:
                    info = m.groupdict()
                    info["file"] = pos[-1]
                    info["page"] = page
                    if info["pkg"] is None:
                        del info["pkg"]
                        prefix = ""
                    else:
                        prefix = ("(%s)" % info["pkg"])
                    prefix = prefix.ljust(m.start("text"))
                    text = [info["text"]]
                continue

            # Bad box messages

            m = re_badbox.match(line)
            if m:
                if boxes:
                    mpos = { "file": pos[-1], "page": page }
                    m = re_atline.search(line)
                    if m:
                        md = m.groupdict()
                        for key in "line", "last":
                            if md[key]: mpos[key] = md[key]
                        line = line[:m.start()]
                    d = {
                        "kind": "warning",
                        "text": line
                        }
                    d.update( mpos )
                    yield d
                skipping = 1
                continue

            # If there is no message, track source names and page numbers.

            last_file = self.update_file(line, pos, last_file)
            page = self.update_page(line, page)

    def get_errors (self):
        return self.parse(errors=1)
    def get_boxes (self):
        return self.parse(boxes=1)
    def get_references (self):
        return self.parse(refs=1)
    def get_warnings (self):
        return self.parse(warnings=1)

    def update_file (self, line, stack, last):
        """
        Parse the given line of log file for file openings and closings and
        update the list `stack'. Newly opened files are at the end, therefore
        stack[1] is the main source while stack[-1] is the current one. The
        first element, stack[0], contains the value None for errors that may
        happen outside the source. Return the last file from which text was
        read (the new stack top, or the one before the last closing
        parenthesis).
        """
        m = re_file.search(line)
        while m:
            if line[m.start()] == '(':
                last = m.group("file")
                stack.append(last)
            else:
                last = stack[-1]
                del stack[-1]
            line = line[m.end():]
            m = re_file.search(line)
        return last

    def update_page (self, line, before):
        """
        Parse the given line and return the number of the page that is being
        built after that line, assuming the current page before the line was
        `before'.
        """
        ms = re_page.findall(line)
        if ms == []:
            return before
        return int(ms[-1]) + 1


########################################################################
# Main
########################################################################

def main():
    TeXCompiler.main()

if __name__ == "__main__":
    main()

