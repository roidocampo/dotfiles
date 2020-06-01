
if has('mac') 
  let s:plugin_dir = fnamemodify(expand('<sfile>'), ':h')
  let s:python_file = s:plugin_dir . '/skim_helper.py' 

  let s:plugin_dir = fnameescape(s:plugin_dir)
  let s:python_file = fnameescape(s:python_file)

  execute 'pyxfile '.s:python_file
  execute 'pythonx skim_helper()'
endif 
