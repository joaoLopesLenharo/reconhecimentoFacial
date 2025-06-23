-- MySQL Workbench Synchronization
-- Generated: 2025-06-23 09:23
-- Model: New Model
-- Version: 1.0
-- Project: Name of the project
-- Author: joao

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

CREATE SCHEMA IF NOT EXISTS `mydb` DEFAULT CHARACTER SET utf8 ;

CREATE TABLE IF NOT EXISTS `mydb`.`alunos` (
  `Id` INT(11) NOT NULL,
  `Nome` VARCHAR(90) NOT NULL,
  `reconhecimento_aluno_id_rn` INT(11) NOT NULL,
  PRIMARY KEY (`Id`),
  INDEX `fk_alunos_reconhecimento_aluno1_idx` (`reconhecimento_aluno_id_rn` ASC) VISIBLE,
  CONSTRAINT `fk_alunos_reconhecimento_aluno1`
    FOREIGN KEY (`reconhecimento_aluno_id_rn`)
    REFERENCES `mydb`.`reconhecimento_aluno` (`id_rn`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

CREATE TABLE IF NOT EXISTS `mydb`.`presencas` (
  `id_lancamento` INT(11) NOT NULL AUTO_INCREMENT,
  `id_aluno` INT(11) NOT NULL,
  `local` VARCHAR(90) NOT NULL,
  PRIMARY KEY (`id_lancamento`),
  INDEX `id_aluno_idx` (`id_aluno` ASC) VISIBLE,
  CONSTRAINT `id_aluno`
    FOREIGN KEY (`id_aluno`)
    REFERENCES `mydb`.`alunos` (`Id`)
    ON DELETE NO ACTION
    ON UPDATE CASCADE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

CREATE TABLE IF NOT EXISTS `mydb`.`reconhecimento_aluno` (
  `id_rn` INT(11) NOT NULL,
  `infoRec` VARCHAR(200) NOT NULL,
  PRIMARY KEY (`id_rn`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
