from enum import Enum

from pydantic import BaseModel


class SubmissionState(Enum):
    SUBMISSION_STATE_UNSPECIFIED = (
        "SUBMISSION_STATE_UNSPECIFIED"  # this shloud never be returned.
    )
    NEW = "NEW"  # student never acessed this submission
    CREATED = "CREATED"  # has been created
    TURNED_IN = "TURNED_IN"  # has been turned in to the teacher
    RETURNED = "RETURNED"  # has been turned in to the student
    RECLAIMED_BY_STUDENT = (
        "RECLAIMED_BY_STUDENT"  # student chose to "unsubmit" the assignment
    )


class CourseWorkType(Enum):
    COURSE_WORK_TYPE_UNSPECIFIED = "COURSE_WORK_TYPE_UNSPECIFIED"  # No work type specified. This is never returned.
    ASSIGNMENT = "ASSIGNMENT"  # An assignment.
    SHORT_ANSWER_QUESTION = "SHORT_ANSWER_QUESTION"  # A short answer question.
    MULTIPLE_CHOICE_QUESTION = "MULTIPLE_CHOICE_QUESTION"  # A multiple-choice question.


class DriveFile(BaseModel):
    id: str
    title: str
    alternateLink: str
    thumbnailUrl: str | None = None


class YouTubeVideo(BaseModel):
    id: str
    title: str
    alternateLink: str
    thumbnailUrl: str | None = None


class Link(BaseModel):
    url: str
    title: str | None = None
    thumbnailUrl: str | None = None


class Form(BaseModel):
    formUrl: str
    responseUrl: str | None = None
    title: str
    thumbnailUrl: str | None = None


# Attachment types
class Attachment(BaseModel):
    driveFile: DriveFile | None = None
    youTubeVideo: YouTubeVideo | None = None
    link: Link | None = None
    form: Form | None = None


# Submission content types
class AssignmentSubmission(BaseModel):
    attachments: list[Attachment] | None = None


class ShortAnswerSubmission(BaseModel):
    answer: str


class MultipleChoiceSubmission(BaseModel):
    answer: str


class Submission(BaseModel):
    courseId: str  # Identifier of the course. Read-only.
    courseWorkId: str  # Identifier for the course work this corresponds to. Read-only.
    id: str  # Classroom-assigned Identifier for the student submission. Unique among submissions for the relevant course work. Read-only.
    userId: str  # Identifier for the student that owns this submission. Read-only.
    creationTime: str  # Creation time of this submission in RFC3339 UTC format (e.g., "2014-10-02T15:01:23Z"). May be unset if student hasn't accessed the item. Read-only.
    updateTime: str  # Last update time of this submission in RFC3339 UTC format. May be unset if student hasn't accessed the item. Read-only.
    state: SubmissionState  # State of this submission. Read-only.
    late: bool = False  # Whether this submission is late. Read-only.
    draftGrade: float | None = (
        None  # Optional pending grade. Non-negative. Decimal values allowed but rounded to two decimal places. Only visible to and modifiable by course teachers.
    )
    assignedGrade: float | None = (
        None  # Optional final grade. Non-negative. Decimal values allowed but rounded to two decimal places. May be modified only by course teachers.
    )
    alternateLink: (
        str  # Absolute link to the submission in the Classroom web UI. Read-only.
    )
    courseWorkType: (
        CourseWorkType  # Type of course work this submission is for. Read-only.
    )
    associatedWithDeveloper: bool = False  # Whether this student submission is associated with the Developer Console project making the request. Read-only.
    # submissionHistory: list[SubmissionHistory]  # The history of the submission (includes state and grade histories). Read-only.

    # Submission content union field - only one of these will be populated based on courseWorkType
    assignmentSubmission: AssignmentSubmission | None = (
        None  # Submission content for ASSIGNMENT type
    )
    shortAnswerSubmission: ShortAnswerSubmission | None = (
        None  # Submission content for SHORT_ANSWER_QUESTION type
    )
    multipleChoiceSubmission: MultipleChoiceSubmission | None = (
        None  # Submission content for MULTIPLE_CHOICE_QUESTION type
    )
