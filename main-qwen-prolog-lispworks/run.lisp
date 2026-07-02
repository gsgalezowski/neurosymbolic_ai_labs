(let* ((root (make-pathname :name nil :type nil :defaults *load-pathname*))
       (log (merge-pathnames "lispworks-run.log" root)))
  (with-open-file (stream log
                          :direction :output
                          :if-exists :supersede
                          :external-format :utf-8)
    (format stream "run.lisp loaded~%")
    (finish-output stream)
    (handler-case
        (progn
          (load (merge-pathnames "orchestrator.lisp" root))
          (format stream "orchestrator loaded~%")
          (finish-output stream)
          (let ((status (neuro-qwen:main)))
            (format stream "finished status=~D~%" status)
            (finish-output stream)
            (lw:quit :status status)))
      (error (condition)
        (format stream "startup error: ~A~%" condition)
        (finish-output stream)
        (lw:quit :status 1)))))
