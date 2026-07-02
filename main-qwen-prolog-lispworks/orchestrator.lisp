;;;; LispWorks 8.0 orchestration layer for Qwen/Ollama and SWI-Prolog.
;;;; No Quicklisp dependencies are required.

(defpackage #:neuro-qwen
  (:use #:cl)
  (:export #:main #:run-experiment))

(in-package #:neuro-qwen)

(defparameter *model* "qwen2.5:7b")
(defparameter *ollama-host* "127.0.0.1")
(defparameter *ollama-port* 11434)
(defparameter *swipl*
  "swipl")

(defparameter *project-root*
  (make-pathname :name nil :type nil
                 :defaults (or *load-pathname* *default-pathname-defaults*)))

(defparameter *guard-file* (merge-pathnames "guard.pl" *project-root*))
(defparameter *cases-file* (merge-pathnames "cases.jsonl" *project-root*))
(defparameter *runs-directory* (merge-pathnames "runs\\" *project-root*))

(defparameter *response-schema*
  (concatenate
   'string
   "{\"type\":\"object\",\"additionalProperties\":false,"
   "\"properties\":{"
   "\"case_id\":{\"type\":\"string\"},"
   "\"facts\":{\"type\":\"array\",\"items\":{"
   "\"type\":\"object\",\"additionalProperties\":false,"
   "\"properties\":{\"predicate\":{\"type\":\"string\"},"
   "\"args\":{\"type\":\"array\",\"items\":{\"anyOf\":["
   "{\"type\":\"string\"},{\"type\":\"number\"}]}}},"
   "\"required\":[\"predicate\",\"args\"]}},"
   "\"status\":{\"type\":\"string\",\"enum\":[\"valid\",\"invalid\"]},"
   "\"answer\":{\"type\":\"string\"}},"
   "\"required\":[\"case_id\",\"facts\",\"status\",\"answer\"]}"))

(defun ensure-run-directory ()
  (ensure-directories-exist (merge-pathnames "placeholder" *runs-directory*)))

(defun json-escape (text)
  (with-output-to-string (out)
    (loop for character across text
          do (case character
               (#\" (write-string "\\\"" out))
               (#\\ (write-string "\\\\" out))
               (#\Newline (write-string "\\n" out))
               (#\Return (write-string "\\r" out))
               (#\Tab (write-string "\\t" out))
               (otherwise (write-char character out))))))

(defun json-request (prompt)
  (concatenate
   'string
   (format nil
           "{\"model\":\"~A\",\"prompt\":\"~A\",\"stream\":false,"
           *model* (json-escape prompt))
   "\"format\":" *response-schema*
   ",\"options\":{\"temperature\":0,\"seed\":42}}"))

(defun ascii-octets (text)
  (let ((octets (make-array (length text)
                            :element-type '(unsigned-byte 8))))
    (loop for character across text
          for index from 0
          for code = (char-code character)
          do (when (> code 127)
               (error "HTTP request is intentionally ASCII-only: ~S"
                      character))
             (setf (aref octets index) code))
    octets))

(defun read-all-octets (stream)
  (let ((result (make-array 4096
                            :element-type '(unsigned-byte 8)
                            :adjustable t
                            :fill-pointer 0))
        (buffer (make-array 4096 :element-type '(unsigned-byte 8))))
    (loop for count = (read-sequence buffer stream)
          while (plusp count)
          do (loop for index below count
                   do (vector-push-extend (aref buffer index) result)))
    result))

(defun header-end (octets)
  (loop for index from 0 to (- (length octets) 4)
        when (and (= (aref octets index) 13)
                  (= (aref octets (+ index 1)) 10)
                  (= (aref octets (+ index 2)) 13)
                  (= (aref octets (+ index 3)) 10))
          return (+ index 4)))

(defun http-post-generate (request-body)
  (let* ((body-octets (ascii-octets request-body))
         (header
           (format nil
                   "POST /api/generate HTTP/1.0~C~CHost: ~A:~D~C~CContent-Type: application/json~C~CContent-Length: ~D~C~CConnection: close~C~C~C~C"
                   #\Return #\Linefeed *ollama-host* *ollama-port*
                   #\Return #\Linefeed #\Return #\Linefeed
                   (length body-octets)
                   #\Return #\Linefeed #\Return #\Linefeed
                   #\Return #\Linefeed))
         (header-octets (ascii-octets header)))
    (with-open-stream
        (socket (comm:open-tcp-stream
                 *ollama-host* *ollama-port*
                 :direction :io
                 :element-type '(unsigned-byte 8)
                 :timeout 10
                 :read-timeout 180
                 :write-timeout 30
                 :errorp t))
      (write-sequence header-octets socket)
      (write-sequence body-octets socket)
      (force-output socket)
      (let* ((response (read-all-octets socket))
             (start (header-end response)))
        (unless start
          (error "Invalid HTTP response from Ollama"))
        (subseq response start)))))

(defun write-octets (path octets)
  (with-open-file (stream path
                          :direction :output
                          :if-exists :supersede
                          :element-type '(unsigned-byte 8))
    (write-sequence octets stream)))

(defun write-text (path text)
  (with-open-file (stream path
                          :direction :output
                          :if-exists :supersede
                          :external-format :utf-8)
    (write-string text stream)))

(defun read-text (path)
  (with-open-file (stream path :external-format :utf-8)
    (with-output-to-string (out)
      (loop for line = (read-line stream nil nil)
            while line
            do (write-line line out)))))

(defun json-string-field (json field)
  (let* ((needle (format nil "\"~A\":\"" field))
         (start (search needle json)))
    (when start
      (let* ((value-start (+ start (length needle)))
             (end (position #\" json :start value-start)))
        (and end (subseq json value-start end))))))

(defun load-cases (&optional limit)
  (with-open-file (stream *cases-file* :external-format :utf-8)
    (loop for line = (read-line stream nil nil)
          for number from 1
          while line
          while (or (null limit) (<= number limit))
          collect line)))

(defun model-input-json (case-json)
  (let ((start (search ",\"expected_status\":" case-json)))
    (if start
        (concatenate 'string (subseq case-json 0 start) "}")
      case-json)))

(defun base-prompt (case-json)
  (concatenate
   'string
   "You normalize a source record into facts. Return only the JSON object "
   "required by the supplied schema. Copy every source_facts item exactly, "
   "without adding, deleting, renaming or changing any fact. Set case_id from "
   "the source. Decide whether the record is logically valid. "
   "Use status valid or invalid and give a short ASCII English answer.\n"
   "SOURCE RECORD:\n" (model-input-json case-json)))

(defun self-check-prompt (case-json)
  (concatenate
   'string
   (base-prompt case-json)
   "\nBefore returning JSON, silently check chronology, age constraints, "
   "required archival metadata, access levels, deadlines and negative fees."))

(defun correction-prompt (case-json violations)
  (concatenate
   'string
   (base-prompt case-json)
   "\nA symbolic validator found these violations: " violations
   ". Correct only status and answer. Facts must still exactly copy source_facts."))

(defun run-prolog (case-path response-path output-base)
  (multiple-value-bind (status output)
      (sys:call-system-showing-output
       (list *swipl* "-q"
             "-s" (namestring *guard-file*)
             "-g" "main"
             "-t" "halt"
             "--"
             (namestring case-path)
             (namestring response-path)
             (namestring output-base))
       :output-stream nil
       :show-cmd nil)
    (declare (ignore output))
    (unless (or (null status) (zerop status))
      (warn "SWI-Prolog returned status ~A" status))))

(defun read-decision (path)
  (with-open-file (stream path :external-format :utf-8)
    (loop for line = (read-line stream nil nil)
          while line
          for split = (position #\= line)
          when split
            collect (cons (subseq line 0 split)
                          (subseq line (1+ split))))))

(defun decision-value (key decision)
  (cdr (assoc key decision :test #'string=)))

(defun safe-name (text)
  (map 'string
       (lambda (character)
         (if (or (alphanumericp character) (char= character #\-))
             character
           #\_))
       text))

(defun generate-and-validate (case-json variant prompt run-root suffix)
  (let* ((case-id (or (json-string-field case-json "id") "unknown"))
         (stem (format nil "~A_~A_~A"
                       (safe-name case-id)
                       (safe-name variant)
                       suffix))
         (case-path (merge-pathnames (format nil "~A.case.json" stem) run-root))
         (response-path
           (merge-pathnames (format nil "~A.ollama.json" stem) run-root))
         (output-base (merge-pathnames stem run-root))
         (decision-path
           (merge-pathnames (format nil "~A.decision" stem) run-root)))
    (write-text case-path case-json)
    (write-octets response-path
                  (http-post-generate (json-request prompt)))
    (run-prolog case-path response-path output-base)
    (values (read-decision decision-path) stem)))

(defun csv-cell (value)
  (let ((text (or value "")))
    (format nil "\"~A\""
            (with-output-to-string (out)
              (loop for character across text
                    do (if (char= character #\")
                           (write-string "\"\"" out)
                         (write-char character out)))))))

(defun write-result-row (stream variant case-id initial final decision)
  (format stream "~{~A~^,~}~%"
          (mapcar #'csv-cell
                  (list variant
                        case-id
                        initial
                        final
                        (decision-value "symbolic_status" decision)
                        (decision-value "model_status" decision)
                        (decision-value "violations" decision)))))

(defun run-variant (case-json variant run-root csv)
  (let* ((case-id (or (json-string-field case-json "id") "unknown"))
         (prompt (if (string= variant "self-check")
                     (self-check-prompt case-json)
                   (base-prompt case-json))))
    (multiple-value-bind (decision stem)
        (generate-and-validate case-json variant prompt run-root "initial")
      (declare (ignore stem))
      (let ((action (decision-value "action" decision)))
        (cond
         ((not (string= variant "neurosymbolic"))
          (write-result-row csv variant case-id action "published" decision))
         ((string= action "accept")
          (write-result-row csv variant case-id action "accepted" decision))
         ((string= action "reject")
          (write-result-row csv variant case-id action "rejected" decision))
         (t
          (let ((violations (decision-value "violations" decision)))
            (multiple-value-bind (corrected corrected-stem)
                (generate-and-validate
                 case-json variant
                 (correction-prompt case-json violations)
                 run-root "corrected")
              (declare (ignore corrected-stem))
              (write-result-row
               csv variant case-id action
               (if (string= (decision-value "action" corrected) "accept")
                   "corrected"
                 "rejected")
               corrected)))))))))

(defun run-experiment (&key limit)
  (ensure-run-directory)
  (let* ((run-name (format nil "run-~D\\" (get-universal-time)))
         (run-root (merge-pathnames run-name *runs-directory*))
         (summary (merge-pathnames "summary.csv" run-root))
         (cases (load-cases limit)))
    (ensure-directories-exist (merge-pathnames "placeholder" run-root))
    (with-open-file (csv summary
                         :direction :output
                         :if-exists :supersede
                         :external-format :utf-8)
      (write-line
       "variant,case_id,initial_action,final_action,symbolic_status,model_status,violations"
       csv)
      (dolist (case-json cases)
        (dolist (variant '("baseline" "self-check" "neurosymbolic"))
          (format t "~&[~A] ~A~%" variant
                  (json-string-field case-json "id"))
          (finish-output)
          (run-variant case-json variant run-root csv))))
    (format t "~&Summary: ~A~%" (namestring summary))
    summary))

(defun command-line-limit ()
  (let ((value (lw:environment-variable "NEURO_LIMIT")))
    (cond
     ((or (null value) (string= value "")) 1)
     ((string-equal value "all") nil)
     (t (parse-integer value)))))

(defun main ()
  (handler-case
      (progn
        (run-experiment :limit (command-line-limit))
        0)
    (error (condition)
      (format *error-output* "~&ERROR: ~A~%" condition)
      1)))
