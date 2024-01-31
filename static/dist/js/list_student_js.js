$(document).ready(function () {
  const loaderOverlay = $(".loader-overlay");

  $('#session-year-dropdown').select2({
    placeholder: 'Select session year',
    allowClear: true,
    minimumInputLength: 1
  });

  $('#course-dropdown').select2({
    placeholder: 'Select course',
    allowClear: true,
    minimumInputLength: 1
  });

  // Fetch session years and populate the dropdown
  $.get(getSessionYear, function (data) {
    var sessionYears = data;
    console.log(data)
    var dropdown = $('#session-year-dropdown');
    $.each(sessionYears, function (index, yearData) {
      console.log(yearData.text)
      dropdown.append($('<option>').text(yearData.text).val(yearData.id));
    });
  });

  // Fetch courses and populate the dropdown
  $.get(getCourse, function (data) {
    var course = data;
    console.log(data)
    var dropdown = $('#course-dropdown');
    $.each(course, function (index, courseData) {
      console.log(courseData.text)
      dropdown.append($('<option>').text(courseData.text).val(courseData.id));
    });
  });

  function fetchStudentsByFilters(sessionYear, course) {
    $.ajax({
      url: filterStudentsUrl,
      type: 'POST',
      data: {
        session_year: sessionYear,
        course: course
      },
      dataType: 'json',
      success: function (student_data) {
        console.log("Student Data: " + student_data)
        if (student_data == false) {
          console.log("Inside if block")
          $(".loader-overlay").css("display", "none");
          showErrorDialog('No Students data found.');
        }
        else {
          console.log("Inside else")

          setStudentData(student_data)
        }

      },
      error: function (xhr, status, error) {
        loaderOverlay.css("display", "none");
        console.error(error);
      }
    });
  }

  $('#fetch-students-button').click(function () {
    var selectedSessionYear = $('#session-year-dropdown').val();
    var selectedCourse = $('#course-dropdown').val();
    loaderOverlay.css("display", "flex");
    fetchStudentsByFilters(selectedSessionYear, selectedCourse);
  });

  $('#search-input').click(function () {
    if ($("#search-input_box").val() != '') {
      $(".loader-overlay").css("display", "flex");

      searchData($("#search-input_box").val())
    }
  });
});

$("#search-input_box").keypress(function (event) {
  if (event.which === 13) {
    event.preventDefault();
    $(".loader-overlay").css("display", "flex");
    if ($("#search-input_box").val() != '') {
      searchData($("#search-input_box").val())
    }
    $("#search-input_box").val("");
  }
});

function searchData(searchTerm) {
  $.ajax({
    url: searchStudentUrl,
    type: 'POST',
    data: { search_term: searchTerm },
    dataType: 'json',
    success: function (student_data) {
      console.log(student_data)
      if (student_data == false) {
        $(".loader-overlay").css("display", "none");
        showErrorDialog('No Students data found.');
      }
      else {
        $("#search-input_box").val("")
        setStudentData(student_data)
      }
    },
    error: function (xhr, status, error) {
      $(".loader-overlay").css("display", "none");
      showErrorDialog(error);
    }
  });
}

function setStudentData(student_data) {
  $(".loader-overlay").css("display", "none");
  console.log("setStudentData: " + student_data)
  var studentTableBody = $('#student-table-body');
  studentTableBody.empty();
  var updateStudentFeeBaseURL = '/update_student_fee/';
  console.log("Inside the setStudentData method")
  $.each(student_data, function (index, student) {
    var row = $('<tr>');
    var updateStudentFeeURL = updateStudentFeeBaseURL + student.id + '/';
    row.append($('<td>').html('<img class="img-circle" src="' + student['profile_pic'] + '" style="width:40px; height: 40px;" />'));
    row.append($('<td>').html("<a href='" + updateStudentFeeURL + "' class='text-primary student-link'>" + student['admin.first_name'] + "</a>"));
    row.append($('<td>').text(student['admin.last_name']));
    row.append($('<td>').text(student['admin.email']));
    row.append($('<td>').text(student['address']));
    row.append($('<td>').text(student['gender']));
    row.append($('<td>').text(student['session_year']));
    row.append($('<td>').text(student['course_name']));
    row.append($('<td>').text(student['date_joined']));
    row.append($('<td>').text(student['total_amount']));
    row.append($('<td>').text(student['amount_paid']));
    row.append($('<td>').text(student['last_due_date']));
    studentTableBody.append(row);
  });
}

function showErrorDialog(message) {
  const errorDialog = document.getElementById('error-dialog');
  const errorMessage = document.getElementById('error-message');
  errorMessage.textContent = message;
  errorDialog.style.display = 'block';
}

// Function to close the error dialog
function closeErrorDialog() {
  const errorDialog = document.getElementById('error-dialog');
  errorDialog.style.display = 'none';
}
