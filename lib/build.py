#!/usr/bin/env python3

from kninja import *
import sys
import os.path

# Project Definition
# ==================

proj = KProject()
proj.build(proj.extdir('kore', '.git'), 'git-submodule-init')

# Non-standard rules needed for K in K
# ------------------------------------

kore_from_config = proj.rule( 'kore-from-config'
                            , description = 'Extracting <kore> cell'
                            , command = 'lib/kore-from-config $cell $in $out'
                            , ext = 'kore'
                            )
kore_parser = proj.rule( 'kore-parser'
                       , description = 'kore-parser'
                       , command     = 'stack build kore:exe:kore-parser && stack exec -- kore-parser $in > $out'
                       )
def kore_exec(kore, ext = 'kore-exec'):
    return proj.rule( 'kore-exec'
                    , description = 'kore-exec'
                    , command     = 'stack build kore:exe:kore-exec && stack exec -- kore-exec $kore --module FOOBAR --pattern $in > $out'
                    ) \
                    .variables(kore = kore) \
                    .implicit(kore)

# Kore to K Pipeline
# ------------------

ekore = proj.source('ekore.md') \
            .then(proj.tangle().output(proj.tangleddir('ekore.k')))
kore = proj.source('kore.k')
kink = proj.source('kink.md') \
           .then(proj.tangle().output(proj.tangleddir('kink.k'))) \
           .then(proj.kompile()
                        .implicit([kore, ekore])
                        .variables( backend = 'java'
                                  , directory = proj.builddir('kink')
                                  , flags = '-I . --syntax-module EKORE-SYNTAX'
                                  ))

def foobar_test(file):
    proj.source(file) \
        .then(kink.krun()) \
        .then(kore_from_config.variables(cell = 'k')) \
        .then(proj.check(proj.source('t/foobar.ekore.expected'))
                     .variables(flags = '--ignore-all-space')) \
        .default()
# foobar_test('t/foobar-backtick-synax.ekore')
foobar_test('t/foobar-frontend-modules.ekore')
foobar_test('t/foobar-declare-sorts.ekore')
foobar_test('t/foobar.ekore.expected')

# These tests are to make sure we can still parse IMP
proj.source('imp/imp.ekore0').then(kink.krun()).default()
proj.source('imp/imp.ekore1').then(kink.krun()).default()

