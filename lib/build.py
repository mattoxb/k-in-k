#!/usr/bin/env python3

from kninja import *
import sys
import os.path

# Helpers
# =======

def test_kfront_to_kore(proj, kdef, testfile):
    out = kdef.krun( output = proj.builddir(testfile + '.out')
                   , input  = testfile + ''
                   )
    kore = proj.build( outputs = proj.builddir(testfile + '.kore')
                     , rule = 'kore-from-config'
                     , inputs = out
                     )
    proj.build( outputs = proj.builddir(testfile + '.kore.ast')
              , rule    = 'kore-parser'
              , inputs  = kore
              )
    kdef.check_actual_expected(os.path.basename(testfile), kore, testfile + '.expected')
    return kore

# Project Definition
# ==================

proj = KProject()
proj.build_ocaml()

# Building Kore & Kore Support
# ----------------------------

### Submodule init update

# TODO: Figure out how to avoid calling `stack build` all the time.
proj.rule( 'kore-parser'
         , description = 'kore-parser'
         , command     = 'stack build kore:exe:kore-parser && stack exec -- kore-parser $in > $out'
         )
proj.rule( 'kore-exec'
         , description = 'kore-exec'
         , command     = 'stack build kore:exe:kore-exec && stack exec -- kore-exec $kore --module FOOBAR --pattern $in > $out'
         )
proj.build(proj.extdir('kore', '.git'), 'git-submodule-init')

# Buiding k-light
# ---------------
proj.build(proj.klightrepodir('.git'), 'git-submodule-init')


proj.rule( 'build-klight'
         , description = 'building k-light'
         , command     = 'cd $klightrepodir && mvn package -DskipTests'
         )

# TODO: Figure out how to make dependence on source java files and not pom
proj.build( inputs    = proj.klightrepodir('pom.xml')
          , rule      = 'build-klight'
          , outputs   = proj.klightbindir('k-light2k5.sh')
          , implicit  = None
          , variables = { 'klightrepodir' : proj.klightrepodir()
                        }
          )


# Converting Frontend Definitions
# -------------------------------

kink = proj.kdefinition( 'kink'
                       , main = proj.tangle('kink.md', proj.tangleddir('kink/kink.k'))
                       , backend = 'ocaml'
                       , alias = 'kink'
                       , kompile_flags = '-I .'
                       )
proj.rule( 'kore-from-config'
         , description = 'Extracting <kore> cell'
         , command = 'lib/kore-from-config $in $out'
         )
foobar_kore = test_kfront_to_kore(proj, kink, 'foobar/foobar.kfront')

# Building and running definitions using the K5/Java translation
# --------------------------------------------------------------

foobar_k5 = proj.kdefinition( 'foobar-k5'
                            , main = 'foobar/foobar.k'
                            , backend = 'kore'
                            , alias = 'foobar-k5'
                            , kompile_flags = '--syntax-module FOOBAR'
                            )
bar_kast = foobar_k5.kast( output = proj.builddir('foobar/programs/bar.foobar.kast')
                         , input  =               'foobar/programs/bar.foobar'
                         , kast_flags = '--kore'
                         )
out = proj.build( inputs  = bar_kast
                , rule    = 'kore-exec'
                , outputs = proj.builddir('foobar/programs/bar.foobar.kink.out')
                , implicit = foobar_kore
                , variables = { 'kore' : foobar_kore
                              }
                )
test = foobar_k5.check_actual_expected('foobar/programs/bar.foobar.kink', out, 'foobar/programs/bar.foobar.expected')
proj.default(test)

out = proj.build( inputs  = bar_kast
                , rule    = 'kore-exec'
                , outputs = proj.builddir('foobar/programs/bar.foobar.k5.out')
                , implicit = 'foobar/foobar.handwritten.kore'
                , variables = { 'kore' : 'foobar/foobar.handwritten.kore'
                              }
                )
test = foobar_k5.check_actual_expected('foobar/programs/bar.foobar.handwritten', out, 'foobar/programs/bar.foobar.expected')
proj.default(test)

# Buliding the eKore transformations
# ----------------------------------

outerk_k5 = proj.tangle( input = 'outer-k.md'
                       , output = proj.tangleddir('outer-k.k5.k')
                       , variables = { "tangle_selector" : ".k5" }
                       )

# TODO: The k-light parser extracts the name of the main module from the
# name of the file. Change this behavior to accept name of module to parse using.
outerk_klight = proj.tangle( input = 'outer-k.md'
                           , output = proj.tangleddir('outer-k.k')
                           , variables = { "tangle_selector" : ".k-light" }
                           )

ekore_def  = proj.kdefinition( 'ekore'
                             , main = proj.tangle('ekore.md', proj.tangleddir('ekore/ekore.k'))
                             , implicit = [ outerk_k5 ]
                             , backend = 'java'
                             , alias = 'ekore'
                             , kompile_flags = '-I ' + proj.tangleddir() + ' --syntax-module EKORE-SYNTAX'
                             )

# Foobar parsing using outer kore
# ----------------------------

parsed_foobar = ekore_def.krun( output = proj.builddir('foobar/foobar.ekoreMinus1')
                              , input = 'foobar/foobar.ekoreMinus1'
                              )

proj.build( inputs = parsed_foobar
          , rule = 'phony'
          , outputs = proj.builddir('foobar/foobar.ekoreMinus1.parses')
          )

# Imp parsing using outer kore
# ----------------------------

parsed_imp = ekore_def.krun( output = proj.builddir('imp/imp.ekoreMinus1.out')
                           , input = 'imp/imp.ekoreMinus1'
                           )
proj.build( inputs = parsed_imp
          , rule = 'phony'
          , outputs = proj.builddir('imp/imp.ekoreMinus1.parses')
          )

proj.default(proj.builddir('imp/imp.ekoreMinus1.parses'))
