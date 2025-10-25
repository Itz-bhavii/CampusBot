package com.training.training.Repositorys;

import java.util.List;
import java.util.UUID;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.training.training.Entities.ChatMessage;


@Repository
public interface ChatMessageRepository extends JpaRepository<ChatMessage,UUID>{

    List<ChatMessage> findByConversationIdOrderByTimestampAsc(UUID conversationId);
}
