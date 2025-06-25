from package.databases.models.project import Project
from sqlmodel import Session, select
from package.utils.utils import now_utc
from fastapi import HTTPException

class ProjectManagement:
    def __init__(self):
        pass

    def create_project(self, project: Project, session: Session):
        # Check for unique project name
        if session.exec(select(Project).where(Project.name == project.name)).first():
            session.close()
            raise HTTPException(status_code=400, detail="Project name already exists.")

        session.add(project)
        session.commit()
        session.refresh(project)
        session.close()
        return project
    
    def read_project(self, project_id: str, session: Session):
        statement = select(Project).where(Project.id == project_id)
        project = session.exec(statement).one_or_none()
        session.close()
        return project

    def update_project(self, project: Project, session: Session):
        project.updated_at = now_utc()
        session.add(project)
        session.commit()
        session.refresh(project)
        session.close()
        return project

    def delete_project(self, project: Project, session: Session):
        session.delete(project)
        session.commit()
        session.close()
        return project