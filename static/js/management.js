var questionCount = document.querySelectorAll('.question-builder').length;

function addQuestion() {
  var idx = questionCount;
  var container = document.getElementById('questionsContainer');
  if (!container) return;

  var div = document.createElement('div');
  div.className = 'question-builder';
  div.dataset.index = idx;
  div.innerHTML = [
    '<div class="question-builder-header">',
    '  <span class="question-builder-num">Question ' + (idx + 1) + '</span>',
    '  <button type="button" class="btn-remove-question" onclick="removeQuestion(this)">Remove</button>',
    '</div>',
    '<div class="form-group">',
    '  <label class="form-label">Question Text *</label>',
    '  <textarea name="question_text" class="form-input form-textarea form-textarea-sm" placeholder="Enter your question here..." required></textarea>',
    '</div>',
    '<div class="answers-builder">',
    '  <label class="form-label">Answer Options (mark the correct one)</label>',
    '  <div class="answer-builder-row">',
    '    <input type="radio" name="correct_' + idx + '" value="0" class="answer-correct-radio" checked>',
    '    <input type="text" name="answer_' + idx + '" class="form-input answer-input" placeholder="Answer option 1">',
    '  </div>',
    '  <div class="answer-builder-row">',
    '    <input type="radio" name="correct_' + idx + '" value="1" class="answer-correct-radio">',
    '    <input type="text" name="answer_' + idx + '" class="form-input answer-input" placeholder="Answer option 2">',
    '  </div>',
    '  <div class="answer-builder-row">',
    '    <input type="radio" name="correct_' + idx + '" value="2" class="answer-correct-radio">',
    '    <input type="text" name="answer_' + idx + '" class="form-input answer-input" placeholder="Answer option 3">',
    '  </div>',
    '  <div class="answer-builder-row">',
    '    <input type="radio" name="correct_' + idx + '" value="3" class="answer-correct-radio">',
    '    <input type="text" name="answer_' + idx + '" class="form-input answer-input" placeholder="Answer option 4">',
    '  </div>',
    '</div>'
  ].join('\n');

  container.appendChild(div);
  questionCount++;
}

function removeQuestion(btn) {
  var card = btn.closest('.question-builder');
  if (card) card.remove();
}
