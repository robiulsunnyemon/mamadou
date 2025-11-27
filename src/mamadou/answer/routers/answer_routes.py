
from fastapi import APIRouter, HTTPException, status
from typing import List

from fastapi.params import Depends

from mamadou.answer.models.answer_model import AnswerModel
from mamadou.answer.schemas.answer_schemas import AnswerCreate, AnswerUpdate, AnswerResponse
from mamadou.auth.models.user_model import UserModel
from mamadou.leader_board.models.leader_board_model import LeaderBoardModel
from mamadou.progress_lesson.models.progress_lesson_model import ProgressLessonModel
from mamadou.question.models.question_model import QuestionModel
from mamadou.utils.user_info import get_user_info

router = APIRouter(prefix="/answers", tags=["answers"])


# GET all answers
@router.get("/", response_model=List[AnswerResponse], status_code=status.HTTP_200_OK)
async def get_all_answers(skip: int = 0, limit: int = 10):
    """
    Get all answers with pagination
    """
    answers = await AnswerModel.find_all().skip(skip).limit(limit).to_list()
    return answers


# GET answer by ID
@router.get("/{id}", response_model=AnswerResponse, status_code=status.HTTP_200_OK)
async def get_answer(id: str):
    """
    Get answer by ID
    """
    answer = await AnswerModel.get(id)
    if not answer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Answer not found")
    return answer


@router.post("/", response_model=AnswerResponse, status_code=status.HTTP_201_CREATED)
async def create_answer(answer_data: AnswerCreate, user: dict = Depends(get_user_info)):
    user_id = user["user_id"]
    db_user = await UserModel.get(user_id)  # await যোগ করুন
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    """
    Create a new answer with lesson progress and update leaderboard
    """
    # Get the question to check correct answer
    db_question = await QuestionModel.get(answer_data.question_id)
    if not db_question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Check if user already submitted this question - Beanie syntax ঠিক করুন
    db_submitted_answer = await AnswerModel.find_one(
        AnswerModel.question_id == answer_data.question_id,
        AnswerModel.user_id == user_id
    )

    # Check if answer is correct
    score = 1 if db_question.correct_answer == answer_data.submit_answer else 0

    # Handle leaderboard score adjustment for existing answer
    old_score = 0
    if db_submitted_answer:
        # Get the old score before updating
        old_score = db_submitted_answer.score

        # Update the existing answer
        db_submitted_answer.submit_answer = answer_data.submit_answer
        db_submitted_answer.right_answer = db_question.correct_answer
        db_submitted_answer.score = score
        await db_submitted_answer.save()  # save()

        answer = db_submitted_answer
    else:
        # Create new answer record
        answer = AnswerModel(
            user_id=user_id,
            course_id=db_question.course_id,
            lesson_id=db_question.lesson_id,
            question_id=answer_data.question_id,
            submit_answer=answer_data.submit_answer,
            right_answer=db_question.correct_answer,
            score=score
        )
        await answer.insert()

    # Update leaderboard
    db_leaderboard = await LeaderBoardModel.find_one(
        LeaderBoardModel.user_id == user_id
    )

    if db_leaderboard:
        # Adjust leaderboard score: subtract old score and add new score
        if db_submitted_answer:
            # For update: subtract old score and add new score
            db_leaderboard.total_score = db_leaderboard.total_score - old_score + score
        else:
            # For new answer: just add the score
            db_leaderboard.total_score += score
        await db_leaderboard.save()
    else:
        # Create new leaderboard entry
        leaderboard_data = LeaderBoardModel(
            user_id=user_id,
            total_score=score
        )
        await leaderboard_data.insert()

    # Calculate progress after creating/updating the answer
    db_questions = await QuestionModel.find(
        QuestionModel.lesson_id == db_question.lesson_id
    ).to_list()

    total_questions = len(db_questions)

    # Get all answers for this lesson and user - Beanie syntax ঠিক করুন
    db_lesson_answers = await AnswerModel.find(
        AnswerModel.lesson_id == db_question.lesson_id,
        AnswerModel.user_id == user_id
    ).to_list()

    # Remove duplicates by question_id to get unique answered questions
    unique_answered_questions = {}
    for ans in db_lesson_answers:
        unique_answered_questions[ans.question_id] = ans

    total_answered = len(unique_answered_questions)

    # Calculate correct progress percentage
    progress_percentage = 0
    if total_questions > 0:
        progress_percentage = (total_answered / total_questions) * 100

    # Check if progress record exists - Beanie syntax
    db_progress = await ProgressLessonModel.find_one(
        ProgressLessonModel.lesson_id == db_question.lesson_id,
        ProgressLessonModel.user_id == user_id
    )

    if db_progress:
        # Update existing progress
        db_progress.progress = progress_percentage
        await db_progress.save()
    else:
        # Create new progress record
        progress_data = ProgressLessonModel(
            lesson_id=db_question.lesson_id,
            progress=progress_percentage,
            user_id=user_id
        )
        await progress_data.insert()

    return answer










# PATCH update answer
@router.patch("/{id}", response_model=AnswerResponse,status_code=status.HTTP_200_OK)
async def update_answer(id: str, answer_data: AnswerUpdate):
    
    """
    Update answer information
    """
    answer = await AnswerModel.get(id)
    if not answer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Answer not found")

    update_data = answer_data.model_dump(exclude_unset=True)
    await answer.update({"$set": update_data})
    return await AnswerModel.get(id)

# DELETE answer
@router.delete("/{id}",status_code=status.HTTP_200_OK)
async def delete_answer(id: str):
    
    """
    Delete answer by ID
    """
    answer = await AnswerModel.get(id)
    if not answer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Answer not found")

    await answer.delete()
    return {"message": "Answer deleted successfully"}
