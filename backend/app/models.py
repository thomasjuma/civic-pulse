from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ArticleBase(BaseModel):
    title: str
    source: str
    summary: str
    full_text: str
    date: str
    image: str = ""
    source_url: str | None = None


class ArticleCreate(ArticleBase):
    pass


class Article(ArticleBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class SubscriberUpsert(BaseModel):
    clerk_user_id: str | None = None
    email: EmailStr
    whatsapp_number: str = Field(min_length=7)
    has_whatsapp_consent: bool


class Subscriber(BaseModel):
    id: int
    clerk_user_id: str | None
    email: EmailStr
    whatsapp_number: str
    has_whatsapp_consent: bool
    consented_at: str | None


class IngestionResult(BaseModel):
    candidates_found: int
    articles_processed: int
    whatsapp_messages_sent: int

